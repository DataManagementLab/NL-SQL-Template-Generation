#!/usr/bin/env python3
""" read a ppdb file and export as json for faster loading
"""

import json


def read_ppdb(ppdb_file):
    """
    read ppdb file and convert into dict look up table with unique value list containing paraphrases

    :param str ppdb_file: path to ppdb file
    :return dict: processed content of ppdb file
    """

    paraphrase_dict = {}

    with open(ppdb_file) as open_in_file:
        for line in open_in_file:
            columns = line.strip().split(' ||| ')
            paraphrases = paraphrase_dict.setdefault(columns[1], [])
            if columns[2] not in paraphrases:
                paraphrases.append(columns[2])

    return paraphrase_dict


if __name__ == '__main__':
    """ read an original ppdb file under 'in_file' and write json to out_file
    """

    in_file = '../data/ppdb/ppdb-2.0-s-all'
    out_file = '../data/ppdb/ppdb.json'

    ppdb_dict = read_ppdb(in_file)

    with open(out_file, 'w') as open_out_file:
        json.dump(ppdb_dict, open_out_file, sort_keys=True, indent=4, separators=(',', ': '))
