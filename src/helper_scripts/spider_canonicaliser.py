#!/usr/bin/env python3
""" canonicalize SQL queries in data available in Spider format
"""
import json
from itertools import groupby
from operator import itemgetter

from nltk import word_tokenize

from db.database import Database
from query.canonicaliser import make_canonical


def canonicalize_spider_queries(spider_path, queries, out_path, preserve_input=True):
    """ canonicalize SQL queries in spider format

    :param str spider_path: path to spider root folder
    :param list queries: data as read from the spider json file
    :param str out_path: filename and path for the output
    :param bool preserve_input: do not change input variables, requires more time and memory
    """

    out_json = []

    # iterate over tuples of db name and all queries for that db
    for db in groupby(queries, itemgetter('db_id')):
        database = Database(db[0], spider_path + db[0], None, spider_path + 'tables.json')

        for original_query in db[1]:

            if preserve_input:
                query = original_query.deepcopy()
            else:
                query = original_query

            sql_complete = make_canonical(' '.join(query['query_toks_no_value']), database.umich_schema, [])
            sql_complete_filled = make_canonical(query['query'], database.umich_schema, [])

            try:
                sql_label = database.parse_query(sql_complete_filled)
            except (KeyError, AssertionError):
                print('\nERROR PARSING SQL\nDB:{}\nQ:{}\nNQ:{}\n'.format(db[0], query['query'], sql_complete_filled))
                print('DB:{}\nQ:{}\nNQ:{}\n'.format(db[0], query['query'], sql_complete_filled),
                      file=open('malformed_canon.txt', 'a'))
                continue

            query['query_toks_no_value'] = word_tokenize(sql_complete)
            query['query'] = sql_complete_filled
            query['query_toks'] = word_tokenize(sql_complete_filled)
            query['sql'] = sql_label

            out_json.append(query)

    with open(out_path, 'w') as out_file:
        json.dump(out_json, out_file, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':

    # path to Spider files
    spider_root = '../data/spider/'

    # standard spider splits as usage example
    for split in ['train_spider', 'train_others', 'dev']:
        with open(spider_root + split + '.json') as in_file:
            split_data = json.load(in_file)

        canonicalize_spider_queries(spider_root, split_data, spider_root + split + '_canon.json', False)
