# PatInv: Machine Translation Testing via Pathological Invariance

PatInv is a representative testing methodology for machine translation software. The key insight of PatInv is that sentences with different meanings should not have the same translation. The implementation is mainly based on NLTK, BERT, and constituency/dependency parsers.

Environment for running the code:

To set up BERT, you could refer to Hugging Face's [implementation](https://github.com/huggingface/transformers) in PyTorch.

To set up language parsers:
+ Download the [core NLP libarary](http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip).
+ Unzip the file and open the folder.
+ Run `java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -ServerProperties props.properties -preload tokenize,ssplit,pos,lemma,ner,parse -status_port 9000 -port 9000`

Read more information about PatInv from the following paper:

+ Shashij Gupta, Pinjia He, Clara Meister, Zhendong Su. [Machine Translation Testing via Pathological Invariance](https://pinjiahe.github.io/papers/ESECFSE20.pdf), *ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE)*, 2020.
