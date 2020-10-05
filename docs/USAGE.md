# Usage Instructions

## Preparation

Before you begin please follow these steps (and repeat whenever changes to resources make them necessary). You'll find more detailed information in the README of the helper_scripts directory:
* if you have a mySQL dump instead of a SQLite database, use mysql2sqlite.sh to convert it
* create ppdb.json through ppdb_preprocess.py
* create your .schema file through schema_generate.py
* verify your templates file through verify_templates.py

## Data
Most of the data folder is exempt from this repository. To generate samples, place:
* your database in a corresponding directory beneath it. This should include the .schema file and (if available) your sqlite database.
* ppdb.json created by helper_scripts/ppdb_preprocess.py under data/ppdb/
Please check parameter descriptions and default values for other necessary changes.

## Data generation

```
python generation/generate.py -db <DB>
```
* Options (filtering hyper-parameters, pipeline modifiers etc) are listed in `generator/generate.py`. Run ``python generate.py -h`` for descriptions.
* Please note that the script has to be executed from the source code directory.
* An exemplary script for running experiments is provided in ```runner.py```.
