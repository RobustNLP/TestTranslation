# RTI: Testing Machine Translation via Referential Transparency

RTI is a inspired by a concept in functional programming: referential transparency. 

To set up language parsers:
+ Download the [core NLP libarary](http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip).
+ Unzip the file and open the folder.
+ Run `java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -ServerProperties props.properties -preload tokenize,ssplit,pos,lemma,ner,parse -status_port 9000 -port 9000`


Read more information about RTI from the following paper:

+ Pinjia He, Clara Meister, Zhendong Su. [Testing Machine Translation via Referential Transparency](https://pinjiahe.github.io/papers/ICSE21.pdf), *International Conference on Software Engineering (ICSE)*, 2021.
