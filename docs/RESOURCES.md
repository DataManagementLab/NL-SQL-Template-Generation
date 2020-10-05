# Resources

## PPDB

This project uses the PPDB 2.0 paraphrasing database.
````tex
@inproceedings{pavlick2015ppdb,
  title={PPDB 2.0: Better paraphrase ranking, fine-grained entailment relations, word embeddings, and style classification},
  author={Pavlick, Ellie and Rastogi, Pushpendre and Ganitkevitch, Juri and Van Durme, Benjamin and Callison-Burch, Chris},
  booktitle={Proceedings of the 53rd Annual Meeting of the Association for Computational Linguistics and the 7th International Joint Conference on Natural Language Processing (Volume 2: Short Papers)},
  volume={2},
  pages={425--430},
  year={2015}
}
````

## Acknowledgements:
- The generator code is based on [nl2sql](https://github.com/sriniiyer/nl2sql) by Srinivasan Iyer
- Pre-processing and evaluation benchmarks from [text2sql-data](https://github.com/jkkummerfeld/text2sql-data) by Finegan-Dollak et al.


## Slot-filling dictionary

The slot-filling dictionary is a text file used to fill placeholders in natural language queries from a group of syntactically interchangeable words. 
This file may also contain empty lines and comment lines (prefixed with #).

Each line specifies a name for the group, encased in {}, followed by =\> and the words/phrases in the group separated through |. 


## Adjective Dictionary

For paraphrasing adjectives, ```compsubadj.pickle``` provides a manually create dictionary of adjectives, their comparative and superlative forms and their polarization.
