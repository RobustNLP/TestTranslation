# SIT: Structure-Invariant Testing for Machine Translation

### Environment for running the code:

To set up BERT, you could refer to Hugging Face's [implementation](https://github.com/huggingface/transformers) in PyTorch.

To set up language parsers:
+ Download the [core NLP libarary](http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip).
+ Unzip the file and open the folder.
+ Run `java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9001  -port 9001 -timeout 15000`
