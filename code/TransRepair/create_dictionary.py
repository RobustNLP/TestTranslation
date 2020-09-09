import spacy
import numpy as np
from scipy import spatial
from collections import defaultdict
from nltk.corpus import words

valid_eng_words = set(words.words())

# Download glove at https://nlp.stanford.edu/projects/glove/, unzip, and put files in GLOVE_LOCATION
GLOVE_LOCATION = "./"
SIM_DICT_FILE = "similarity_dict.txt"


glove_dict = {}
with open(GLOVE_LOCATION + "glove.6B.200d.txt", 'r') as f:
    for line in f:
        values = line.split()
        word = values[0]
        vector = np.asarray(values[1:], "float32")
        glove_dict[word] = vector

print(len(glove_dict))
def get_glove_vec(word):
	return glove_dict[word]

# install spacy and download model with `python -m spacy download en_core_web_md`
spacy_dict = spacy.load('en_core_web_md')

def get_spacy_vec(word):
	return spacy_dict(word).vector

def similarity(vec1, vec2):
	return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

print("creating dictionary...")

filtered_words = []

similarity_dict = defaultdict(list)
spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS
for word in sorted(glove_dict.keys()):
	if len(word) < 3 or not word in valid_eng_words\
		or word not in spacy_dict.vocab or np.count_nonzero(get_spacy_vec(word)) == 0:
		continue
	
	for other_word in glove_dict.keys():
		# already encountered...
		if other_word <= word or not other_word in valid_eng_words\
		    or other_word not in spacy_dict.vocab or np.count_nonzero(get_spacy_vec(other_word)) == 0 or word in spacy_stopwords:
			continue
		similarity1 = similarity(get_glove_vec(word), get_glove_vec(other_word))
		similarity2 = similarity(get_spacy_vec(word), get_spacy_vec(other_word))

		if similarity1 > 0.8 and similarity2 > 0.8:
			print('here')
			similarity_dict[word].append(other_word)
			similarity_dict[other_word].append(word)
	print(word)

# def to_file(d):
#     return '\n'.join("%s %s" % (key, ' '.join(map(str, values))) for key, values in d.items())

# with open(SIM_DICT_FILE, 'w') as f:
# 	f.write(to_file(similarity_dict))

def to_line(k, v):
    return ("%s %s" % (k, ' '.join(map(str, v))))

with open(SIM_DICT_FILE, 'w') as f:
	for key, values in similarity_dict.items():
		currentLine = to_line(key, values)
		f.write(currentLine+'\n')







