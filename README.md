# Machine Translation Testing

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

A list of suspicious issues. Each issue contains a pair of sentences in source language and their translations.

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


### Get started

Code organization:

+ [code](./code): the machine translation testing package
+ [dataset](./dataset): seed sentences for translation testing.



### Feedback
For any questions or feedback, please post to [the issue page](https://github.com/RobustNLP/TestTranslation/issues). 



