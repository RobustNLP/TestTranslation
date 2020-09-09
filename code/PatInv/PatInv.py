import nltk
import numpy as np
import torch
import pickle
from pytorch_pretrained_bert import BertTokenizer, BertModel, BertForMaskedLM
import string
from nltk.tokenize.treebank import TreebankWordTokenizer, TreebankWordDetokenizer
from bert_embedding import BertEmbedding
import nltk
from nltk.corpus import stopwords
from nltk.corpus import words
import os, requests, uuid, json
from google.cloud import translate_v2 as translate
import urllib.request, urllib.error, urllib.parse
from bs4 import BeautifulSoup
import re
import json
from apted import APTED
from apted.helpers import Tree
from nltk.parse import CoreNLPParser
from nltk.stem import WordNetLemmatizer
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import wordnet
from use.use import UseSimilarity

def perturb(sentence, bertmodel, num):
	"""Generate a list of similar sentences by BERT
	
	Arguments:
	sentence: Sentence which needs to be perturbed
	bertModel: MLM model being used (BERT here)
	num: Number of perturbations required for a word in a sentence
	"""

	# Tokenize the sentence
	tokens = tokenizer.tokenize(sent)
	pos_inf = nltk.tag.pos_tag(tokens)

	# the elements in the lists are tuples <index of token, pos tag of token>
	bert_masked_indexL = list()

	# collect the token index for substitution
	for idx, (word, tag) in enumerate(pos_inf):
		if (tag.startswith("JJ") or tag.startswith("JJR") or tag.startswith("JJS")
			or tag.startswith("PRP") or tag.startswith("PRP$") or  tag.startswith("RB")
			or tag.startswith("RBR") or tag.startswith("RBS") or tag.startswith("VB") or
			tag.startswith("VBD") or tag.startswith("VBG") or tag.startswith("VBN") or
			tag.startswith("VBP") or tag.startswith("VBZ") or tag.startswith("NN") or
			tag.startswith("NNS") or tag.startswith("NNP") or tag.startswith("NNPS")):

			tagFlag = tag[:2]

			if (idx!=0 and idx!=len(tokens)-1):
				bert_masked_indexL.append((idx, tagFlag))

	bert_new_sentences = list()

	# generate similar setences using Bert
	if bert_masked_indexL:
		bert_new_sentences = perturbBert(sent, bertmodel, num, bert_masked_indexL)
	return bert_new_sentences


def perturbBert(sent, model, num, masked_indexL):
	"""Generate a list of similar sentences by Bert
	
	Arguments:
	sent: sentence which need to be perturbed
	model: MLM model
	num: Number of perturbation for each word
	masked_indexL: List of indexes which needs to be perturbed
	"""

	global num_words_perturb
	new_sentences = list()
	tokens = tokenizer.tokenize(sent)

	# set of invalid characters
	invalidChars = set(string.punctuation)

	# for each idx, use Bert to generate k (i.e., num) candidate tokens
	for (masked_index, tagFlag) in masked_indexL:
		original_word = tokens[masked_index]
		# Getting the base form of the word to check for it's synonyms
		low_tokens = [x.lower() for x in tokens]		
		low_tokens[masked_index] = '[MASK]'
		# Eliminating cases for "'s" as Bert does not work well on these cases.		
		if original_word=="'s":
			continue
		# Eliminating cases of stopwords
		if original_word in stopWords:
			continue
		# try whether all the tokens are in the vocabulary
		try:
			indexed_tokens = berttokenizer.convert_tokens_to_ids(low_tokens)
			tokens_tensor = torch.tensor([indexed_tokens])
			prediction = model(tokens_tensor)

		except KeyError as error:
			print ('skip sent. token is %s' % error)
			continue
		
		# Get the similar words
		topk_Idx = torch.topk(prediction[0, masked_index], num)[1].tolist()
		topk_tokens = berttokenizer.convert_ids_to_tokens(topk_Idx)
		num_words_perturb += 1
		# Remove the tokens that only contains 0 or 1 char (e.g., i, a, s)
		topk_tokens = list(filter(lambda x:len(x)>1, topk_tokens))
		# Remove the cases where predicted words are synonyms of the original word or both words have same stem.
		# generate similar sentences
		for x in range(len(topk_tokens)):
			t = topk_tokens[x]
			if any(char in invalidChars for char in t):
				continue
			tokens[masked_index] = t
			new_pos_inf = nltk.tag.pos_tag(tokens)

			# only use the similar sentences whose similar token's tag is still JJ, JJR, JJS, PRP, PRP$, RB, RBR, RBS, VB, VBD, VBG, VBN, VBP, VBZ, NN, NNP, NNS or NNPS
			if (new_pos_inf[masked_index][1].startswith(tagFlag)):
				new_sentence = detokenizer.detokenize(tokens)
				new_sentences.append(new_sentence)
		tokens[masked_index] = original_word

	return new_sentences

def generate_syntactically_similar_sentences_replace(num_of_perturb, dataset):
	"""Generate syntactically similar sentences for each sentence in the dataset.
	For PaInv-Replace
	Returns dictionary of original sentence to list of generated sentences
	"""
	# Use nltk treebank tokenizer and detokenizer
	tokenizer = TreebankWordTokenizer()
	detokenizer = TreebankWordDetokenizer()

	# Stopwords from nltk
	stopWords = list(set(stopwords.words('english')))

	# File from which sentences are read
	file = open(dataset, "r")

	# when we use Bert
	berttokenizer = BertTokenizer.from_pretrained('bert-large-uncased')
	bertmodel = BertForMaskedLM.from_pretrained('bert-large-uncased')
	bertmodel.eval()

	# Number of perturbations you want to make for a word in a sentence
	dic = {}
	num_of_perturb = 50
	num_sent = 0
	for line in file:
		s_list = line.split("\n")
		source_sent = s_list[0]
		# Generating new sentences using BERT
		new_sents = perturb(source_sent, bertmodel, num_of_perturb)
		dic[line] = new_sents		
		if new_sents != []:
			num_sent += 1
	return dic

def replacenth(string, sub, wanted, n):
    """Replace nth word in a sentence
    
    string: Complete string
    sub: Substring to be replaced
    wanted: Replace by wanted
    n: index of the occurence of sub to be replaced
    """
    where = [m.start() for m in re.finditer(sub, string)][n-1]
    before = string[:where]
    after = string[where:]
    after = after.replace(sub, wanted, 1)
    newString = before + after
    return newString


def get_all(tree, detokenizer, stopWords):
    """Return all the phrases in the tree"""
    s = set()
    if str(tree)==tree:
        return s
    l = tree.label()
    if not (detokenizer.detokenize(tree.leaves()).lower() in stopWords):
        if (l=="JJR" or l=="JJS" or l=="JJ" or l=="NN" or l=="NNS" or l=="NNP" or l=="NNPS"
            or l=="RB" or l=="RBR" or l=="RBS" or l=="VB" or l=="VBD" or l=="VBG" or l=="VBN"
            or l=="VBP" or l=="VBZ" or l=="NP" or l=="VP" or l=="PP" or l=="ADVP"):
            s.add(detokenizer.detokenize(tree.leaves()))    
    for node in tree:
        s = s | get_all(node)
    return s

def generate_syntactically_similar_sentences_remove(dataset):
    """Generate syntactically similar sentences for each sentence in the dataset.
	for PaInv-Remove
    Returns dictionary of original sentence to list of generated sentences
    """
    # Run CoreNLPPArser on local host
    eng_parser = CoreNLPParser('http://localhost:9000')
    
    # Use nltk treebank tokenizer and detokenizer
    tokenizer = TreebankWordTokenizer()
    detokenizer = TreebankWordDetokenizer()

    # Stopwords from nltk
    stopWords = list(set(stopwords.words('english')))

    # Load dataset
    file = open(dataset,"r")

    dic = {}

    for line in file:
        sent = line.split("\n")[0]
        source_tree = eng_parser.raw_parse(sent)
        dic[line] = []
        for x in source_tree:
            phrases = get_all(x, detokenizer, stopWords)
            for t in phrases:
                if t=="'s":
                    continue
                for y in range(20):
                    try:
                        new_sent = replacenth(sent,t,"",y+1).replace("  "," ")
                        dic[line].append(sent)
                    except:
                        break
    return dic

def get_wordnet_pos(word):
    """Get pos tags of words in a sentence"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def treeToTree(tree):
    """Compute the distance between two trees by tree edit distance"""
    tree = tree.__str__()
    tree = re.sub(r'[\s]+',' ', tree)
    tree = re.sub('\([^ ]+ ', '(', tree)
    tree = tree.replace('(', '{').replace(')', '}')
    return next(map(Tree.from_text, (tree,)))

def treeDistance(tree1, tree2):
    """Compute distance between two trees"""
    tree1, tree2 = treeToTree(tree1), treeToTree(tree2)
    ap = APTED(tree1, tree2)
    return ap.compute_edit_distance()

def filtering_via_syntactic_and_semantic_information_replace(pert_sent, synonyms):
    """Filter sentences by synonyms and constituency structure for PaInv-Replace.
    Returns a dictionary of original sentence to list of filtered sentences
    """
    stopWords = list(set(stopwords.words('english')))
    syn_dic = {}
    filtered_sent = {}
    stemmer = SnowballStemmer("english")
    lemmatizer = WordNetLemmatizer()

    tokenizer = TreebankWordTokenizer()
    detokenizer = TreebankWordDetokenizer()

    # Run CoreNLPPArser on local host
    eng_parser = CoreNLPParser('http://localhost:9000')

    for original_sentence in list(pert_sent.keys()):
        # Create a dictionary from original sentence to list of filtered sentences
        filtered_sent[original_sentence] = []
        tokens_or = tokenizer.tokenize(original_sentence)
        # Constituency tree of source sentence
        source_tree = [i for i, in eng_parser.raw_parse_sents([original_sentence])]
        # Get lemma of each word of source sentence
        source_lem = [lemmatizer.lemmatize(w, get_wordnet_pos(w)) for w in nltk.word_tokenize(original_sentence)]
        new_sents = pert_sent[original_sentence]
        target_trees_GT = []
        num = 50
        # Generate constituency tree of each generated sentence
        for x in range(int(len(new_sents)/num)):
            target_trees_GT[(x*num):(x*num)+num] = [i for i, in eng_parser.raw_parse_sents(new_sents[(x*num):(x*num)+num])]
        x = int(len(new_sents)/num)
        target_trees_GT[(x*num):] = [i for i, in eng_parser.raw_parse_sents(new_sents[(x*num):])]
        for x in range(len(new_sents)):
            s = new_sents[x]
            target_lem = [lemmatizer.lemmatize(w, get_wordnet_pos(w)) for w in nltk.word_tokenize(s)]
            # If sentence is same as original sentence then filter that
            if s.lower()==original_sentence.lower():
                continue
            # If there constituency structure is not same, then filter
            if treeDistance(target_trees_GT[x],source_tree[0]) > 1:
                continue
            # If original sentence and generate sentence have same lemma, then filter
            if target_lem == source_lem:
                continue
            # Tokens of generated sentence
            tokens_tar = tokenizer.tokenize(s)
            for i in range(len(tokens_or)):
                if tokens_or[i]!=tokens_tar[i]:
                    word1 = tokens_or[i]
                    word2 = tokens_tar[i]
                    word1_stem = stemmer.stem(word1)
                    word2_stem = stemmer.stem(word2)
                    word1_base = WordNetLemmatizer().lemmatize(word1,'v')
                    word2_base = WordNetLemmatizer().lemmatize(word2,'v')
                    # If original word and predicted word have same stem, then filter
                    if word1_stem==word2_stem:
                        continue
                    # If they are synonyms of each other, the filter
                    syn1 = synonyms(word1_base)
                    syn2 = synonyms(word2_base)
                    if (word1 in syn2) or (word1_base in syn2) or (word2 in syn1) or (word2_base in syn1):
                        continue
                    if ((word1 in stopWords) or (word2 in stopWords) or (word1_stem in stopWords)
                        or (word2_stem in stopWords) or (word1_base in stopWords) or (word2_base in stopWords)):
                        continue
                    filtered_sent[original_sentence].append(s)
    return filtered_sent

def filtering_via_syntactic_and_semantic_information_remove(syntactically_similar_sentences, threshold):
    """Filtering if the difference between length of original and generated sentence is < threshold
    Returns a dictionary of original sentence to list of filtered sentences
    """
    filtered_sent = {}
    for sent in syntactically_similar_sentences.keys():
        filtered_sent[sent] = []
        for similar_sent in syntactically_similar_sentences[sent]:
            if len(sent) - len(similar_sent) > threshold:
                filtered_sent[sent].append(similar_sent)
    return filtered_sent

def filter_by_sentence_embeddings(sentences_dic, threshold):
	"""Filter sentence by ensuring similarity less than threshold
	Returns dictionary of original sentence to list og filtered sentences
	"""
	filtered_sentences = {}
	similarity_model = UseSimilarity('USE')
	for original_sent, generated_sents in enumerate(sentences_dic):
		filtered_sentences[original_sent] = []
		for sent in generated_sents:
			if similarity_model.get_sim([original_sent, sent]) < threshold:
				filtered_sentences[original_sent].append(sent)
	return filtered_sentences

def BingTranslate(api_key, filtered_sent, language_from, language_to):
    """Bing Microsoft translator

    If you encounter any issues with the base_url or path, make sure
    that you are using the latest endpoint:
    https://docs.microsoft.com/azure/cognitive-services/translator/reference/v3-0-translate
    
    Arguments:
    api_key = Bing Microsoft Translate API key
    filtered_sent = dictionary of original sentence to list of filtered sentences
    language_from = Source language code
    language_to = Target language code

    returns translation dictionary from source sentence to target sentence
    """
    base_url = 'https://api.cognitive.microsofttranslator.com'
    path = '/translate?api-version=3.0'
    params = '&language='+ language_from +'&to=' + language_to
    constructed_url = base_url + path + params

    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    
    text = []

    for or_sent, filtered_sents in enumerate(filtered_sent):
        text.append(or_sent)
        text.extend(filtered_sents)

    body = [{'text': x} for x in text]
    # You can pass more than one object in body.
    
    request = requests.post(constructed_url, headers=headers, json=body)
    response = request.json()

    translation_dic = {}
    for i in range(len(text)):
        translation_dic[text[i]] = response[i]["translations"][0]["text"].replace('&#39;',"'").replace('&quot;',"'")
    return translation_dic

def GoogleTranslate(filtered_sent, source_language, target_language):
    """Google Translate, visit https://cloud.google.com/translate/docs to know pre-requisites
    
    Arguments:
    filtered_sent = dictionary of original sentence to list of filtered sentences
    source_language = Source language code
    target_language = Target language code

    returns translation dictionary from source sentence to target sentence
    """
    translate_client = translate.Client()
    translation_dic = {}
    
    for sent in filtered_sent.keys():
        sent1 = sent.split("\n")[0]
        ref_translation = ""
        ref_translation = translate_client.translate(sent1,target_language=target_language,
                                                     source_language=source_language)['translatedText'].replace('&#39;', "'").replace('&quot;', "'")
        translation_dic[sent] = ref_translation
        for new_s in filtered_sent[sent]:
            new_ref_translation = translate_client.translate(new_s,target_language=target_language,
                                                             source_language=source_language)['translatedText'].replace('&#39;',"'").replace('&quot;',"'")
            translation_dic[new_s] = new_ref_translation
    return translation_dic    

def collect_target_sentences(translator, filtered_sent, source_language, target_language, api_key=None):
    """Return Translation dic for a translator"""
    if translator == 'Google':
        return GoogleTranslate(filtered_sent, source_language, target_language)
    if translator == 'Bing':
        return BingTranslate(api_key, filtered_sent, source_language, target_language)

def detecting_translation_errors(filtered_sent, translation_dic, filename):
    """Detect translation errors by comparing translation of original sentence with
    generated sentence

    filtered_sent: dictionary of original sentence to list of filtered sentences
    translation_dic: Dictionary of sentence to its tranlation
    filename: File's name where suspected issues will be wrote
    """
    f = open(filename, "a")
    for sent in filtered_sent.keys():
        sent1 = sent.split("\n")[0]
        ref_translation = translation_dic[sent]
        for new_s in filtered_sent[sent]:
            new_ref_translation = translation_dic[new_s]
            if ref_translation==new_ref_translation:
                f.write(sent)
                f.write(new_s)
                f.write(ref_translation)
                f.write(" ")
    f.close()

########################Main code#############################

# Path of dataset to be used to find translation errors
dataset = "dataset/business"
# Bing Translate
bing_translate_api_key = 'enter the API key for Bing Microsoft Translate'

# target language: Chinese
bing_source_language = 'en'
bing_target_language = 'zh-Hans'

# Google Translate

# target language: Hindi
google_source_language = 'en'
google_target_language = 'hi'

########################PaInv-Replace#########################

num_of_perturb = 50 # Number of perturbation for each word in the sentence

syntactically_similar_sentences = generate_syntactically_similar_sentences_replace(num_of_perturb, dataset)

# File where a dictionary of generated sentences corresponding to original sentence will be saved
with open("data/business_bert_output_replace.dat", 'wb') as f:
	pickle.dump(syntactically_similar_sentences, f)

# Load dictionary of synonyms for each word
with open("data/synonyms.dat", 'rb') as f:
	synonyms = pickle.load(f)

# Filtering by synonyms and filtering by constituency structure
filtered_sentences = filtering_via_syntactic_and_semantic_information_replace(syntactically_similar_sentences,
	                                                                          synonyms)

# File where a dictionary of filtered sentences corresponding to original sentence will be saved
with open("data/business_filter_output_replace.dat", 'wb') as f:
	pickle.dump(filtered_sentences, f)

# optional step: filtering by sentence embeddings

threshold = 0.9    # Choose threshold for filtering

# Run install_USE.sh and install Universal sentence encoder before running the code below
filtered_sentences = filter_by_sentence_embeddings(filtered_sentences, threshold)

# File where a dictionary of filtered sentences corresponding to original sentence will be saved
with open("data/business_filter_output_replace.dat", 'wb') as f:
	pickle.dump(filtered_sentences, f)

target_sentences_bing = collect_target_sentences("Bing", filtered_sentences,
	                                             bing_source_language, bing_target_language,
	                                             bing_translate_api_key)

# Save translations locally for later use
with open("data/business_chinese_replace_bing.dat", 'wb') as f:
    pickle.dump(target_sentences_bing, f)

target_sentences_google = collect_target_sentences("Google", filtered_sentences,
	                                               google_source_language, google_target_language)

# Save translations locally for later use
with open("data/business_hindi_replace_google.dat", 'wb') as f:
    pickle.dump(target_sentences_google, f)

filename = "business_chinese_errors_bing"

# Write translation errors in filename
detecting_translation_errors(filtered_sentences, target_sentences_bing, filename)


filename = "business_hindi_errors_google"

# Write translation errors in filename
detecting_translation_errors(filtered_sentences, target_sentences_google, filename)

###################################PaInv-Remove###########################

syntactically_similar_sentences = generate_syntactically_similar_sentences_remove(dataset)

# File where a dictionary of generated sentences corresponding to original sentence will be saved
with open("data/business_bert_output_remove.dat", 'wb') as f:
	pickle.dump(syntactically_similar_sentences, f)

threshold = 6    # Choose threshold for filtering

# Filtering by synonyms and filtering by constituency structure
filtered_sentences = filtering_via_syntactic_and_semantic_information_remove(syntactically_similar_sentences,
	                                                                         threshold)

# File where a dictionary of filtered sentences corresponding to original sentence will be saved
with open("data/business_filter_output_remove.dat", 'wb') as f:
	pickle.dump(filtered_sentences, f)

# File where a dictionary of filtered sentences corresponding to original sentence will be saved
with open("data/business_filter_output_replace.dat", 'wb') as f:
	pickle.dump(filtered_sentences, f)

target_sentences_bing = collect_target_sentences("Bing", filtered_sentences,
	                                             bing_source_language, bing_target_language,
	                                             bing_translate_api_key)

# Save translations locally for later use
with open("data/business_chinese_replace_bing.dat", 'wb') as f:
    pickle.dump(target_sentences_bing, f)

target_sentences_google = collect_target_sentences("Google", filtered_sentences,
	                                               google_source_language, google_target_language)

# Save translations locally for later use
with open("data/business_hindi_replace_google.dat", 'wb') as f:
    pickle.dump(target_sentences_google, f)

filename = "business_chinese_errors_bing"

# Write translation errors in filename
detecting_translation_errors(filtered_sentences, target_sentences_bing, filename)


filename = "business_hindi_errors_google"

# Write translation errors in filename
detecting_translation_errors(filtered_sentences, target_sentences_google, filename)
