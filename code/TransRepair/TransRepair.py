import subprocess
from nltk.tokenize.treebank import TreebankWordTokenizer, TreebankWordDetokenizer
import nltk
import numpy as np
from google.cloud import translate
import jieba
import os, requests, uuid, json

#Bing translation
def BingTranslate(api_key, text, language_from, language_to):
	# If you encounter any issues with the base_url or path, make sure
	# that you are using the latest endpoint: https://docs.microsoft.com/azure/cognitive-services/translator/reference/v3-0-translate
	base_url = 'https://api.cognitive.microsofttranslator.com'
	path = '/translate?api-version=3.0'
	params = '&language='+ language_from +'&to=' + language_to
	constructed_url = base_url + path + params

	headers = {
	    'Ocp-Apim-Subscription-Key': api_key,
	    'Content-type': 'application/json',
	    'X-ClientTraceId': str(uuid.uuid4())
	}
	if type(text) is str:
		text = [text]

	body = [{'text': x} for x in text]
	# You can pass more than one object in body.
	
	request = requests.post(constructed_url, headers=headers, json=body)
	response = request.json()


	return [i["translations"][0]["text"] for i in response]


def getLevenshtein(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros ((size_x, size_y))
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        matrix [0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return (matrix[size_x - 1, size_y - 1])


def normalizedED(seq1, seq2):

	dist = getLevenshtein(seq1, seq2)
	normalized_dist = 1 - (dist/max(len(seq1), len(seq2)))

	return normalized_dist


def getSubSentSimilarity(subsentL1, subsentL2):
	similarity = -1

	for subsent1 in subsentL1:
		for subsent2 in subsentL2:
			currentSim = normalizedED(subsent1.split(' '), subsent2.split(' '))
			if currentSim>similarity:
				similarity = currentSim

	return similarity

def wordDiffSet(sentence1, sentence2):

	file1 = "temptest1.txt"
	file2 = "temptest2.txt"

	set1 = set()
	set2 = set()

	with open(file1, 'w') as f:
		f.write(sentence1)

	with open(file2, 'w') as f:
		f.write(sentence2)

	p = subprocess.run(["wdiff", file1, file2], stdout= subprocess.PIPE)
	wdstr = p.stdout.decode("utf-8")

	# print (wdstr)


	idxL1 = []
	idxL2 = []

	startIdx = -1
	endIdx = -1
	for idx, c in enumerate(wdstr):
		if c=='[':
			startIdx = idx
		elif c==']':
			endIdx = idx
			idxL1.append((startIdx, endIdx))
		elif c=='{':
			startIdx = idx
		elif c=='}':
			endIdx = idx
			idxL2.append((startIdx, endIdx))


	for idxPair in idxL1:
		wordsS = wdstr[idxPair[0]+2:idxPair[1]-1]
		wordsL = wordsS.split(' ')
		set1 |= set(wordsL)

	for idxPair in idxL2:
		wordsS = wdstr[idxPair[0]+2:idxPair[1]-1]
		wordsL = wordsS.split(' ')
		set2 |= set(wordsL)

	return (set1, set2)


def getSubSentenceList(sentence1, sentence2, set1, set2):
	# obtain the diff words
	(set1, set2) = wordDiffSet(sentence1, sentence2)

	# generate sub sentences
	subsentL1 = []
	subsentL2 = []

	removeIdx1 = []
	removeIdx2 = []

	tokenizer = TreebankWordTokenizer()
	detokenizer = TreebankWordDetokenizer()

	sentence1L = tokenizer.tokenize(sentence1)
	sentence2L = tokenizer.tokenize(sentence2)

	for idx, word in enumerate(sentence1L):
		if word in set1:
			removeIdx1.append(idx)

	for idx, word in enumerate(sentence2L):
		if word in set2:
			removeIdx2.append(idx)

	for idx in removeIdx1:
		tokens = tokenizer.tokenize(sentence1)
		tokens.pop(idx)
		subsent = detokenizer.detokenize(tokens)
		subsentL1.append(subsent)

	for idx in removeIdx2:
		tokens = tokenizer.tokenize(sentence2)
		tokens.pop(idx)
		subsent = detokenizer.detokenize(tokens)
		subsentL2.append(subsent)

	return (subsentL1, subsentL2)

def generate_sentences(sent):
	tokens = tokenizer.tokenize(sent)
	pos_inf = nltk.tag.pos_tag(tokens)

	new_sentences, masked_indexes = [], []
	tokens = tokenizer.tokenize(sent)
	for idx, (word, tag) in enumerate(pos_inf):
		if word in sim_dict:
			masked_indexes.append((idx, tag))

	for (masked_index, tag) in masked_indexes:
		original_word = tokens[masked_index]

		# only replace noun, adjective, number
		if tag.startswith('NN') or tag.startswith('JJ') or tag=='CD':		

			# generate similar sentences
			for similar_word in sim_dict[original_word]:
				tokens[masked_index] = similar_word			
				new_pos_inf = nltk.tag.pos_tag(tokens)

				# check that tag is still same type
				if (new_pos_inf[masked_index][1].startswith(tag[:2])):
					new_sentence = detokenizer.detokenize(tokens)
					new_sentences.append(new_sentence)

			tokens[masked_index] = original_word

	return new_sentences

# initialization
tokenizer = TreebankWordTokenizer()
detokenizer = TreebankWordDetokenizer()
dataset = 'business'
software = 'bing'
similarity_threshold = 0.96
translate_client = translate.Client()	# initialize the Google translate client
apikey = 'enter the API key for Bing Microsoft Translate'


# load the similar word dictionary
SIM_DICT_FILE = "similarity_dict.txt"

sim_dict = {}
with open(SIM_DICT_FILE, 'r') as f:
	lines = f.readlines()
	for l in lines:
		sim_dict[l.split()[0]] = l.split()[1:]
print ("created dictionary")


# load input sentences
ori_source_sents = []
with open('../dataset/'+dataset) as file:
	for line in file:
		ori_source_sents.append(line.strip())
print ('input sentences loaded')


# translate input sentences
ori_target_sents = []
for ori_source_sent in ori_source_sents:
	if software=='google':
		# Google translate
		translation = translate_client.translate(
			ori_source_sent,
			target_language='zh-CN',
			source_language='en')
		ori_target_sent = translation['translatedText'].replace("&#39;", "'")
	else:
		# Bing translate
		ori_target_sent = BingTranslate(apikey, ori_source_sent, 'en', 'zh-Hans')[0]
	
	ori_target_sents.append(ori_target_sent)



# for each input sentence, generate similar sentences and test cases
suspicous_issueL = []
count = 0

for ori_source_sent, ori_target_sent in zip(ori_source_sents, ori_target_sents):
	new_sentsL = generate_sentences(ori_source_sent)

	for new_source in new_sentsL:
		# collect the target sent from machine translation software
		if software=='google':
			# Google translate
			translation = translate_client.translate(
				new_source,
				target_language='zh-CN',
				source_language='en')
			new_target = translation['translatedText'].replace("&#39;", "'")
		else:
			# Bing translate
			new_target = BingTranslate(apikey, new_source, 'en', 'zh-Hans')[0]

		# obtain the segmented one for Chinese
		sentence1 = ' '.join(jieba.cut(ori_target_sent))
		sentence2 = ' '.join(jieba.cut(new_target))


		# obtain different words by wdiff
		set1, set2 = wordDiffSet(sentence1, sentence2)

		# get sub sentences
		subsentL1, subsentL2 = getSubSentenceList(sentence1, sentence2, set1, set2)

		similarity = getSubSentSimilarity(subsentL1, subsentL2)


		if similarity!=-1 and similarity<similarity_threshold:
			suspicous_issueL.append((str(count), ori_source_sent, ori_target_sent, new_source, new_target))
			# suspicous_issueL.append((str(count), str(similarity), ori_source_sent, ori_target_sent, new_source, new_target))
			count += 1


writebugs = open('./results/'+dataset+'_'+software+'_bug.txt', 'w')

for (ID, ori_source_sent, ori_target_sent, new_source, new_target) in suspicous_issueL:
	writebugs.write('Issue: '+ID+'\n')
	# writebugs.write(similaritystr+'\n')
	writebugs.write(ori_source_sent+'\n')
	writebugs.write(ori_target_sent+'\n')
	writebugs.write(new_source+'\n')
	writebugs.write(new_target+'\n')

writebugs.close()

