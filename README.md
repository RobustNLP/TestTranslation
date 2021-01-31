# Machine Translation Testing

[![license](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE.md)

This project provides a toolkit for automated machine translation testing, which is the first step towards robust and practical machine translation. By applying the toolkit, users can automatically find translation errors caused by any machine translation models. 

:telescope: If you use any of our tools or datasets in your research for publication, please kindly cite the following papers.
+ [**ICSE'20**] Pinjia He, Clara Meister, Zhendong Su. [Structure-Invariant Testing for Machine Translation](https://arxiv.org/pdf/1907.08710.pdf). *International Conference on Software Engineering (ICSE)*, 2020.
+ [**ESEC/FSE'20**] Shashij Gupta, Pinjia He, Clara Meister, Zhendong Su. [Machine Translation Testing via Pathological Invariance](https://pinjiahe.github.io/papers/ESECFSE20.pdf). *ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE)*, 2020.

### Input:

A list of sentence in source language. For example:

|Sentences:|
| :--- |
| I live on campus with smart people. |
| I like basketball. |

### Output:

A list of suspicious issues. Each issue contains a pair of sentences in source language and their translations. For example (en->zh):

|Suspicious issue 1:|
| :--- |
| I live on campus with smart people. -> 我和聪明的人住在校园里。(Meaning: I live on campus with smart people.) |
| I live on campus with tall people. -> 我住在校园里，身材高大。(Meaning: I live on campus, I am tall.) |

|Suspicious issue 2:|
| :--- |
| I like hiking. -> 我喜欢徒步。(Meaning: I like hiking.) |
| I hate hiking. -> 我喜欢徒步。(Meaning: I like hiking.) |

Note the meanings of the translations (in parentheses) are not part of the output and they are presented here for clarity.

### Testing approach currently available:

| Tools | References |
| :--- | :--- |
| SIT | [**ICSE'20**] [Structure-Invariant Testing for Machine Translation](https://arxiv.org/pdf/1907.08710.pdf), by Pinjia He, Clara Meister, Zhendong Su. |
| TransRepair-ED | [**ICSE'20**] [Automatic Testing and Improvement of Machine Translation](https://arxiv.org/pdf/1910.02688.pdf), by Zeyu Sun, Jie M. Zhang, Mark Harman, Mike Papadakis, Lu Zhang.  |
| PatInv | [**ESEC/FSE'20**] [Machine Translation Testing via Pathological Invariance](https://pinjiahe.github.io/papers/ESECFSE20.pdf), by Shashij Gupta, Pinjia He, Clara Meister, Zhendong Su. |
| SemMT | [**arXiv'20**] [SemMT: A Semantic-based Testing Approach for Machine Translation Systems](https://arxiv.org/abs/2012.01815), by Jialun Cao, Meiziniu Li, Yeting Li, Ming Wen, Shing-Chi Cheung. |
| RTI | [**ICSE'21**] [Testing Machine Translation via Referential Transparency](https://pinjiahe.github.io/papers/ICSE21.pdf), by Pinjia He, Clara Meister, Zhendong Su. |


### Get started

Code organization:

+ [code](./code): the machine translation testing package
+ [dataset](./dataset): seed sentences for translation testing.

APIs provided by Google and Microsoft:

+ For Google Translate, useful tips could be found here: [\[G1\]](https://cloud.google.com/translate/docs/basic/setup-basic)[\[G2\]](https://neliosoftware.com/blog/how-to-generate-an-api-key-for-google-translate/?nab=0&utm_referrer=https%3A%2F%2Fwww.google.com%2F). 
+ For Bing Microsoft Translator, after getting your API key string, you need to copy that into the [apikey](./code/SIT/SIT.py#L171) string (e.g., for SIT). Useful tips: [\[B1\]](https://azure.microsoft.com/en-us/services/cognitive-services/translator-text-api/)[\[B2\]](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/translator-text-how-to-signup)
+ If you intend to test Bing Microsoft Translator using your own approach, the [bingtranslate](./code/SIT/SIT.py#L18) method can be utilized. 

### Feedback
For any questions or feedback, please post to [the issue page](https://github.com/RobustNLP/TestTranslation/issues). 



