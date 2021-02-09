from nltk.parse import CoreNLPParser
from nltk.corpus import stopwords
import numpy as np
import string
import re
from collections import Counter
import os, requests, uuid, json
from google.cloud import translate



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
	# you can pass more than one object in body.
	
	request = requests.post(constructed_url, headers=headers, json=body)
	response = request.json()

	return [i["translations"][0]["text"] for i in response]


# Calculate the frequency of words/chars in the translations of the RTI
# np_super_target: the containing phrase/sentence
# np_sub_target: the RTI
# distance: the distance threshold
# return: True for a suspicious issue
def CheckInvariantDict(np_super_target, np_sub_target, distance):
	violation = False
	currentdistance = 0

	# count the number of every Chinese char
	np_super_targetD = dict(Counter(np_super_target))
	np_sub_targetD = dict(Counter(np_sub_target))

	# count the number of every words
	# np_super_targetD = dict(Counter(np_super_target.split()))
	# np_sub_targetD = dict(Counter(np_sub_target.split()))

	# additional "stop" chars in Chinese
	punctsL = ['“', '”', '，', '·', ' ', ',', '的', '了', "'", '"']
	for pun in punctsL:
		np_sub_targetD.pop(pun, None)


	for key in np_sub_targetD:
		if key not in np_super_targetD:
			currentdistance += np_sub_targetD[key]

		else:
			value_difference = np_sub_targetD[key]-np_super_targetD[key]
			if value_difference > 0:
				currentdistance += value_difference

	# if the distance is larger than a threshold, "True" will be returned to indicate a suspicious issue
	if currentdistance>distance:
		violation = True

	return violation


# An alternative approach that only consider the occurrence of words/chars in the translations of the RTI
# np_super_target: the containing phrase/sentence
# np_sub_target: the RTI
# distance: the distance threshold
# return: True for a suspicious issue
def CheckInvariantSet(np_super_target, np_sub_target, distance):
	violation = False

	# count the number of every Chinese char
	np_super_targetS = set(list(np_super_target))
	np_sub_targetS = set(list(np_sub_target))

	# count the number of every words
	# np_super_targetD = dict(Counter(np_super_target.split()))
	# np_sub_targetD = dict(Counter(np_sub_target.split()))

	# additional "stop" chars in Chinese
	stopS = {'“', '”', '，', '·', ' ', ',', '的', '了', "'", '"'}

	diffS = np_sub_targetS - np_super_targetS

	diffS = diffS - stopS
	
	if len(diffS)>distance:
		violation = True

	return violation


# Find potential RTIs and store in "invariantsD"
# super_node: a non-terminal node in the constituency parse tree
# super_str: the corresponding phrase of the non-terminal node
# invariantsD: a dictionay of RTIs, each key is a containing RTI, each value is a list of RTIs contained by the key
# stopwordsS: a set of stop words
# num_word_th: the maximum length of an RTI
def FindInvariant(super_node, super_str, invariantsD, stopwordsS, num_word_th):

	for node in super_node:

		# check whether it is a leaf node
		if isinstance(node, str):
			continue

		label = node.label()
		if label == 'NP':
			if len(node.leaves()) == 1:
				continue

			# get the corresponding phrase of the non-terminal node
			node_str = ' '.join(node.leaves()).replace(" 's", "'s").replace("-LRB-", "(").replace("-RRB-", ")").strip()
			node_strL = node_str.split()

			num_word_no_stop = len([i for i in node_strL if i not in stopwordsS])

			# if the RTI is not too long and not too short
			if len(node.leaves())<num_word_th and num_word_no_stop>2:	

				if node_str.endswith("'"):
					node_str = node_str[:-1].strip()

				if super_str not in invariantsD:
					invariantsD[super_str] = set([node_str])
				else:
					invariantsD[super_str].add(node_str)

			# recursively search the containing RTIs/sentences
			FindInvariant(node, node_str, invariantsD, stopwordsS, num_word_th)

		FindInvariant(node, super_str, invariantsD, stopwordsS, num_word_th)



# Purity implementation
# output_filename: output file name, the default path is "filename_bugs_distance.txt"
# distance_threshold: the distance threshold
# rtiD: the RTIs found
def RTI(output_filename, distance_threshold, nmtsoftware, rtiD, source_lang, target_lang):
	suspicious_issuesL = []
	non_suspicious_issuesL = []
	numberOfChar = 0

	output_file = output_filename+'_bugs_'+str(distance_threshold)+'.txt'
	write_output = open(output_file, 'w')

	# optional, also output the non_suspicious issues
	# non_suspicious_file = output_filename+'_corrects_'+str(distance_threshold)+'.txt'
	# write_correct = open(non_suspicious_file, 'w')

	translated_count = 0
	# Check each containing RTIs/sentences and its contained RTIs in the dictionary
	for invIdx, np_super in enumerate(rtiD):

		np_subS = rtiD[np_super]

		# For the super phrase

		# If already translated, directly obtain the cache
		if np_super in cached_translationsD:
			np_super_target = cached_translationsD[np_super]

		# If not translated, use API
		else:
			numberOfChar += len(np_super)
			if nmtsoftware=='google':
				# Google translate
				translation = translate_client.translate(
			    	np_super,
			    	target_language=target_lang,
			    	source_language=source_lang)
				np_super_target = translation['translatedText'].replace("&#39;", "'")
			else:
				# Bing translate
				np_super_target = BingTranslate(apikey, np_super, source_lang, target_lang)[0]

			cached_translationsD[np_super] = np_super_target
			translated_count += 1

		# filter some strange translations returned
		if re.search('[a-z]', np_super_target):
			# print ('super illegal:', np_super_target)
			continue

		# For the subset phrase
		for np_sub in np_subS:
			if np_sub in cached_translationsD:
				np_sub_target = cached_translationsD[np_sub]
			else:
				numberOfChar += len(np_sub)
				if nmtsoftware=='google':
					# Google translate
					translation = translate_client.translate(
				    	np_sub,
				    	target_language=target_lang,
				    	source_language=source_lang)
					np_sub_target = translation['translatedText'].replace("&#39;", "'")
				else:
					# Bing translate
					np_sub_target = BingTranslate(apikey, np_sub, source_lang, target_lang)[0]

				cached_translationsD[np_sub] = np_sub_target
				translated_count += 1

			# filter some strange translations returned
			if re.search('[a-z]', np_sub_target):
				# print ('sub illegal:', np_sub_target)
				continue

			# if violates the invariant, then report as a bug
			# violation = CheckInvariantSet(np_super_target, np_sub_target, distance_threshold)
			violation = CheckInvariantDict(np_super_target, np_sub_target, distance_threshold)


			if violation:
				suspicious_issuesL.append( (np_super, np_super_target, np_sub, np_sub_target) )
			# else:
			# 	non_suspicious_issuesL.append((np_super, np_super_target, np_sub, np_sub_target))

	# Print all the issues
	for idx, issue in enumerate(suspicious_issuesL):
		write_output.write('Issue: ' + str(idx) + '\n')
		write_output.write(issue[0] + '\n')
		write_output.write(issue[1] + '\n')
		write_output.write(issue[2] + '\n')
		write_output.write(issue[3] + '\n')


	print ('There are', translated_count, 'API calls.')

	# for idx, issue in enumerate(non_suspicious_issuesL):
	# 	write_correct.write('Issue: ' + str(idx) + '\n')
	# 	write_correct.write(issue[0] + '\n')
	# 	write_correct.write(issue[1] + '\n')
	# 	write_correct.write(issue[2] + '\n')
	# 	write_correct.write(issue[3] + '\n')


	write_output.close()
	# write_correct.close()

	return numberOfChar

########################################################################################################
# Main code
########################################################################################################

# parameters
distance_threshold = 0
dataset = 'business'
software = 'google'
num_word_th = 10
numberOfChar = 0

# initialize a constituency parser
eng_parser =  CoreNLPParser('http://localhost:9000')

# initialize the Google translate client
translate_client = translate.Client()

# input your key for Bing Microsoft translator
apikey = ''

# set original sentence file path
input_file = './data/'+dataset


# for google en->zh
source_lang = 'en'
target_lang = 'zh-CN'

# for bing en-zh
# source_lang = 'en'
# target_lang = 'zh-Hans'

output_filename = dataset+'_'+software

# initialize stop words in the source language
stopwordsS = set(stopwords.words('english'))


# get original sentences from file
ori_source_sents = []
with open(input_file) as file:
	for line in file:
		ori_source_sents.append(line.strip())


# a dictionay of RTIs, each key is a containing RTI, each value is a list of RTIs contained by the key
np_invariantsD = dict()



# parse the original source sentences
ori_source_trees = [i for (i,) in eng_parser.raw_parse_sents(ori_source_sents, properties={'ssplit.eolonly': 'true'})]


# find RTIs
for t, super_str in zip(ori_source_trees, ori_source_sents):
	FindInvariant(t, super_str, np_invariantsD, stopwordsS, num_word_th)

print ('\n invariants constructed\nThere are', len(np_invariantsD), 'invariants. Filtering')


# Since np sometimes could be nearly identical to the original sentence (i.e., only punctuations different), we filter those duplicate pairs here.
chartosent = dict()
for sent in ori_source_sents:
	sent_no_pun = ''.join(sent.translate(str.maketrans('', '', string.punctuation)).strip().split())
	chartosent[sent_no_pun] = sent

# rtiD is the dictionary of RTI pairs
rtiD = dict()
for super_str in np_invariantsD:
	super_str_no_pun = ''.join(super_str.translate(str.maketrans('', '', string.punctuation)).strip().split())

	if super_str_no_pun in chartosent:
		sent = chartosent[super_str_no_pun]
		if sent in rtiD and len(np_invariantsD[super_str])<len(rtiD[sent]):
			continue
		rtiD[sent] = np_invariantsD[super_str]
	else:
		rtiD[super_str] = np_invariantsD[super_str]


print ('\n invariants filtered\nThere are', len(rtiD), 'invariants.')


# translate original sentences
ori_target_sents = []
for ori_source_sent in ori_source_sents:
	if software=='google':
		# Google translate
		translation = translate_client.translate(
			ori_source_sent,
			target_language=target_lang,
			source_language=source_lang)
		ori_target_sent = translation['translatedText'].replace("&#39;", "'")
	else:
		# Bing translate
		ori_target_sent = BingTranslate(apikey, ori_source_sent, source_lang, target_lang)[0]
	
	numberOfChar += len(ori_source_sent)
	ori_target_sents.append(ori_target_sent)


# dictionary to remember all the translated sentences, will be re-used for the invariance check
cached_translationsD = dict()
for source_sent, target_sent in zip(ori_source_sents, ori_target_sents):
	cached_translationsD[source_sent] = target_sent


# detect the translation
tempChar = RTI(output_filename=output_filename, distance_threshold=distance_threshold, nmtsoftware=software, rtiD=rtiD, source_lang=source_lang, target_lang=target_lang)
numberOfChar += tempChar

print ('Number of characters translated:', tempChar)