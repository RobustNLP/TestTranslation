from nltk.parse import CoreNLPDependencyParser
import jieba
import nltk
import Levenshtein
from nltk.data import find
import numpy as np
from google.cloud import translate
import torch
from pytorch_pretrained_bert import BertTokenizer, BertModel, BertForMaskedLM
import string
from nltk.tokenize.treebank import TreebankWordTokenizer, TreebankWordDetokenizer
import time
import pickle
import os, requests, uuid, json


# Bing translation
def bingtranslate(api_key, text, language_from, language_to):
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


# Generate a list of similar sentences by Bert
def perturb(sent, bertmodel, num):
	tokens = tokenizer.tokenize(sent)
	pos_inf = nltk.tag.pos_tag(tokens)

	# the elements in the lists are tuples <index of token, pos tag of token>
	bert_masked_indexL = list()

	# collect the token index for substitution
	for idx, (word, tag) in enumerate(pos_inf):
		# substitute the nouns and adjectives; you could easily substitue more words by modifying the code here
		if (tag.startswith('NN') or tag.startswith('JJ')):
			tagFlag = tag[:2]

			# we do not perturb the first and the last token because BERT's performance drops on for those positions
			if (idx!=0 and idx!=len(tokens)-1):
				bert_masked_indexL.append((idx, tagFlag))

	bert_new_sentences = list()

	# generate similar setences using Bert
	if bert_masked_indexL:
		bert_new_sentences = perturbBert(sent, bertmodel, num, bert_masked_indexL)

	return bert_new_sentences


def perturbBert(sent, bertmodel, num, masked_indexL):
	new_sentences = list()
	tokens = tokenizer.tokenize(sent)

	invalidChars = set(string.punctuation)

	# for each idx, use Bert to generate k (i.e., num) candidate tokens
	for (masked_index, tagFlag) in masked_indexL:
		original_word = tokens[masked_index]

		low_tokens = [x.lower() for x in tokens]		
		low_tokens[masked_index] = '[MASK]'

		# try whether all the tokens are in the vocabulary
		try:
			indexed_tokens = berttokenizer.convert_tokens_to_ids(low_tokens)
			tokens_tensor = torch.tensor([indexed_tokens])
			prediction = bertmodel(tokens_tensor)

		# skip the sentences that contain unknown words
		# another option is to mark the unknow words as [MASK]; we skip sentences to reduce fp caused by BERT
		except KeyError as error:
			print ('skip a sentence. unknown token is %s' % error)
			break
		
		# get the similar words
		topk_Idx = torch.topk(prediction[0, masked_index], num)[1].tolist()
		topk_tokens = berttokenizer.convert_ids_to_tokens(topk_Idx)

		# remove the tokens that only contains 0 or 1 char (e.g., i, a, s)
		# this step could be further optimized by filtering more tokens (e.g., non-english tokens)
		topk_tokens = list(filter(lambda x:len(x)>1, topk_tokens))

		# generate similar sentences
		for t in topk_tokens:
			if any(char in invalidChars for char in t):
				continue
			tokens[masked_index] = t
			new_pos_inf = nltk.tag.pos_tag(tokens)

			# only use the similar sentences whose similar token's tag is still NN or JJ
			if (new_pos_inf[masked_index][1].startswith(tagFlag)):
				new_sentence = detokenizer.detokenize(tokens)
				new_sentences.append(new_sentence)

		tokens[masked_index] = original_word

	return new_sentences

# calculate the distance between 
def depDistance(graph1, graph2):
	
	# count occurences of each type of relationship
	counts1 = dict()
	for i in graph1:
	  counts1[i[1]] = counts1.get(i[1], 0) + 1

	counts2 = dict()
	for i in graph2:
	  counts2[i[1]] = counts2.get(i[1], 0) + 1

	all_deps = set(list(counts1.keys()) + list(counts2.keys()))
	diffs = 0
	for dep in all_deps:
		diffs += abs(counts1.get(dep,0) - counts2.get(dep,0))
	return diffs




########################################################################################################
# Main code
########################################################################################################


# initialize the dependency parser
chi_parser = CoreNLPDependencyParser('http://localhost:9001')

# use nltk treebank tokenizer and detokenizer
tokenizer = TreebankWordTokenizer()
detokenizer = TreebankWordDetokenizer()

# BERT initialization
berttokenizer = BertTokenizer.from_pretrained('bert-large-uncased')
bertmodel = BertForMaskedLM.from_pretrained('bert-large-uncased')
bertmodel.eval()

# initialize the Google translate client
translate_client = translate.Client()

print ('initialized')

# source language: English; target language: Chinese
source_language = 'en'
target_language = 'zh-CN'

# parameters
num_of_perturb = 10			# number of generated similar words for a given position
distance_threshold = 0.0		# the distance threshold in "translation error detection via structure comparison"
issue_threshold = 3			# how many output issues
sentenceBount = 10000			# an upperbound to avoid translating too many sentences
apikey = ''				# the apikey for Bing Microsoft Translator

dataset = 'politics'
software = 'bing'
output_file = 'results_'+dataset+'_'+software+'.txt'
write_output = open(output_file, 'w')

sent_count = 0
issue_count = 0


# load the input source sentences
origin_source_sentsL = []
with open('./data/'+dataset) as file:
	for line in file:
		origin_source_sentsL.append(line.strip())


origin_target_sentsL = []
origin_target_sentsL_seg = []
# translate the input source sentences
if software=='bing':
	# Bing translate
	for source_sent in origin_source_sentsL:
		target_sent = bingtranslate(apikey, source_sent, 'en', 'zh-Hans')[0]
		origin_target_sentsL.append(target_sent)

		target_sent_seg = ' '.join(jieba.cut(target_sent))
		origin_target_sentsL_seg.append(target_sent_seg)

		sent_count += 1
else:
	#Google translate
	for source_sent in origin_source_sentsL:
		translation = translate_client.translate(
		    source_sent,
		    target_language=target_language,
		    source_language=source_language)
		target_sent = translation['translatedText']
		origin_target_sentsL.append(target_sent)

		target_sent_seg = ' '.join(jieba.cut(target_sent)) 
		origin_target_sentsL_seg.append(target_sent_seg)

		sent_count += 1


# parse the segmented original target sentences to obtain dependency parse trees
origin_target_treesL = [i for (i,) in chi_parser.raw_parse_sents(origin_target_sentsL_seg, properties={'ssplit.eolonly': 'true'})]

print ('input sentences translated and parsed.')


# For each input source sentence, generate a list of similar sentences to test
for idx, origin_source_sent in enumerate(origin_source_sentsL):
	#To avoid exceeding the user limit by Google; for Bing, this can be commented
	# time.sleep(4)

	print (idx, origin_source_sent)

	origin_target_sent = origin_target_sentsL[idx]
	origin_target_tree = origin_target_treesL[idx]

	suspicious_issues = list()

	# Get the perturbed sentences
	new_source_sentsL = perturb(origin_source_sent, bertmodel, num_of_perturb)

	if len(new_source_sentsL)==0:
		continue

	print ('number of sentences: ', len(new_source_sentsL))


	new_target_sentsL = list()
	new_target_sents_segL = list()

	if software=='bing':
		# Bing translate
		for new_source_sent in new_source_sentsL:
			new_target_sent = bingtranslate(apikey, new_source_sent, 'en', 'zh-Hans')[0]
			new_target_sentsL.append(new_target_sent)

			new_target_sent_seg = ' '.join(jieba.cut(new_target_sent))
			new_target_sents_segL.append(new_target_sent_seg)

			sent_count += 1
	else:
		#Google translate
		for new_source_sent in new_source_sentsL:
			translation = translate_client.translate(
			    new_source_sent,
			    target_language=target_language,
			    source_language=source_language)
			new_target_sent = translation['translatedText']
			new_target_sentsL.append(new_target_sent)

			new_target_sent_seg = ' '.join(jieba.cut(new_target_sent)) 
			new_target_sents_segL.append(new_target_sent_seg)

			sent_count += 1
	
	print('new source sentences translated')

	# Get the parse tree of the perturbed sentences
	new_target_treesL = [target_tree for (target_tree, ) in chi_parser.raw_parse_sents(new_target_sents_segL, properties={'ssplit.eolonly': 'true'})]
	assert(len(new_target_treesL) == len(new_source_sentsL))
	print('new target sentences parsed')

	for (new_source_sent, new_target_sent, new_target_tree) in zip(new_source_sentsL, new_target_sentsL, new_target_treesL):
		distance = depDistance(origin_target_tree.triples(), new_target_tree.triples()) 

		if distance > distance_threshold:
			suspicious_issues.append((new_source_sent, new_target_sent, distance))
	print('distance calculated')


	# clustering by distance for later sorting
	suspicious_issues_cluster = dict()
	for (new_source_sent, new_target_sent, distance) in suspicious_issues:
		if distance not in suspicious_issues_cluster:
			new_cluster = [(new_source_sent, new_target_sent)]
			suspicious_issues_cluster[distance] = new_cluster
		else:
			suspicious_issues_cluster[distance].append((new_source_sent, new_target_sent))
	print('clustered')

	# if no suspicious issues
	if len(suspicious_issues_cluster) == 0:
		continue

	issue_count += 1

	write_output.write(f'ID: {issue_count}\n')
	write_output.write('Source sent:\n')
	write_output.write(origin_source_sent)
	write_output.write('\nTarget sent:\n')
	write_output.write(origin_target_sent)
	write_output.write('\n\n')

	# sort by distance, from large to small
	sorted_keys = sorted(suspicious_issues_cluster.keys())
	sorted_keys.reverse()

	remaining_issue = issue_threshold
	# Output the top k sentences
	for distance in sorted_keys:
		if remaining_issue == 0:
			break
		candidateL = suspicious_issues_cluster[distance]
		if len(candidateL) <= remaining_issue:
			remaining_issue -= len(candidateL)
			for candidate in candidateL:
				write_output.write('Distance: %f\n' % (distance))
				write_output.write(candidate[0] + '\n' + candidate[1] + '\n')
		else:
			sortedL = sorted(candidateL, key=lambda x: len(x[1]))
			issue_threshold_current = remaining_issue
			for i in range(issue_threshold_current):
				write_output.write('Distance: %f\n' % (distance))
				write_output.write(sortedL[i][0] + '\n' + sortedL[i][1] + '\n')
				remaining_issue -= 1
	write_output.write('\n')

	print('result outputed')

	# stop when translating too many sentences (avoid costing too much)
	if sent_count>sentenceBount:
		print (f'More than {sentenceBount} sentence.')
		break

write_output.close()
