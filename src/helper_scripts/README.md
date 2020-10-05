# Helpers

## General Information

This directory contains helper scripts.

They are not needed for the execution of the actual data generation process, but may help in preparing data etc.

Each script is described below, along with usage instructions.

## Helper Scripts

### Spider Canonicaliser

This script is used to canonicalize the SQL queries is spider formatted data files.
To canonicalize the standard spider files under data/spider simply call

```` python spider_canonicaliser.py ````

The path to the spider base folder and the selection of json files can be changed at the bottom of the file.
Output will be written to the same folder ending in "_canon.json".

If you would like to use the method for different files, the bottom part of the script provides a usage example.

### Schema Generator

This script is used to generate the individual schema files for each DB in the spider dataset from the 'tables.json'.

A location for the 'tables.json' needs to be provided through the *schema* parameter. An output directory can be specified through the *out_dir* parameter.

````python schema_generate.py -schema ../data/spider/tables.json [-out_dir ../data/spider/schemata]````

### DB converter

This bash script converts a mysql dump file to a sqlite3 data base file. Usage is explained in the comments at the top of the file.
