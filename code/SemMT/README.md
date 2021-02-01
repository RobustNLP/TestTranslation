# SemMT: A Semantic-based Testing Approach for Machine Translation Systems

SemMT can effectively detect quantity (e.g., "at least 3 times" and "at most 3 times") and logic (e.g., "include" and "exclude") related mistranslations. SemMT applies round-trip translation and measures the semantic similarity between the original and translated sentences. Its key insight is that the semantics expressed by the logic and numeric constraint can be captured by regular expressions (or deterministic finite automata).

SemMT has been open-source by its authors [here](https://github.com/SemMT-2021/SemMT).

Read more information about SemMT from the following paper:

+ Jialun Cao, Meiziniu Li, Yeting Li, Ming Wen, Shing-Chi Cheung. [SemMT: A Semantic-based Testing Approach for Machine Translation Systems](https://arxiv.org/pdf/2012.01815.pdf), *arXiv*, 2020.
