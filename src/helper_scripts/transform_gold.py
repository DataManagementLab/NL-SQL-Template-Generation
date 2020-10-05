#!/usr/bin/env python3
""" create matching gold SQL file for data json file
"""

import json
import sys

if __name__ == '__main__':

    in_path = sys.argv[1]

    with open(in_path) as in_file:
        data = json.load(in_file)

    with open(in_path[:-5] + '_gold.sql', 'w') as out_file:
        for sample in data:
            out_file.write(f'{sample["query"]}\t{sample["db_id"]}\n')
