# SIT: Structure-Invariant Testing for Machine Translation

### Environment for running the code:
To use Google Translate API and Bing Microsoft Translator API, you need to register corresponding accounts.
+ For Google Translate, useful tips could be found here: [\[G1\]](https://cloud.google.com/translate/docs/basic/setup-basic)[\[G2\]](https://neliosoftware.com/blog/how-to-generate-an-api-key-for-google-translate/?nab=0&utm_referrer=https%3A%2F%2Fwww.google.com%2F). 
+ For Bing Microsoft Translator, after getting your API key string, you need to copy that into the [SIT code](./SIT.py#L171). Useful tips: [\[B1\]](https://azure.microsoft.com/en-us/services/cognitive-services/translator-text-api/)[\[B2\]](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/translator-text-how-to-signup)

To set up BERT, you could refer to Hugging Face's [implementation](https://github.com/huggingface/transformers) in PyTorch.

To set up language parsers:
+ Download the [core NLP libarary](http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip).
+ Unzip the file and open the folder.
+ Run `java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9001  -port 9001 -timeout 15000`
