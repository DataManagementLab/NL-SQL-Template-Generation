#!/usr/bin/env python3
""" generate schema files for all spider DBs
"""
import argparse
import json
import os

TYPES = {'TEXT': 0, 'NUMBER': 1, 'BOOLEAN': 2, 'TIME': 3, 'OTHERS': 4}


# TODO document !!!
def generate_schema_files(schema_file, out_dir):
    """ generates schema files for all DBs listed in the provided file

    :param str schema_file: path to the spider "tables.json" file (or equivalent)
    :param str out_dir: path to the output directory where a directory for each DB will be created
    """

    with open(schema_file) as in_file:
        json_list = json.load(in_file)

    for db in json_list:

        # TODO error handling edge case formula 1
        if db['db_id'] == 'formula_1':
            continue

        print(f'generating schema file for {db["db_id"]}')

        directory = f'{out_dir}/{db["db_id"]}'

        if not os.path.exists(directory):
            os.makedirs(directory)

        schema = {'types': TYPES,
                  'ents': {},
                  'defaults': {db['table_names_original'][i]: {'utt': db['table_names'][i]} for i in
                               range(len(db['table_names']))
                               }
                  }
        j = 0
        for i, table in enumerate(db['table_names_original']):

            if len(db['primary_keys']) > j and db['column_names'][db['primary_keys'][j]][0] == i:
                schema['defaults'][db['table_names_original'][i]]['col'] = \
                    db['column_names_original'][db['primary_keys'][j]][1]
                j += 1

            columns = [col[1] for col in db['column_names_original'] if col[0] == i]
            col_utts = [col[1] for col in db['column_names'] if col[0] == i]
            col_types = [db['column_types'][j] for j in range(len(db['column_names'])) if db['column_names'][j][0] == i]
            column_dict = {columns[j]: {'index': True,
                                        'type': col_types[j].upper(),
                                        'utt': col_utts[j]} for j in range(len(col_utts))}
            schema['ents'][table] = column_dict

        schema['links'] = {table: {} for table in db['table_names_original']}
        equivalencies = set()
        foreign_key_dict = {}
        for i1, i2 in db['foreign_keys']:
            foreign_key_dict[i1] = foreign_key_dict.get(i1, []) + [i2]
            foreign_key_dict[i2] = foreign_key_dict.get(i2, []) + [i1]

        for key in foreign_key_dict:

            foreign_key_dict[key].sort()

            for i, value in enumerate(foreign_key_dict[key]):
                if value > key:
                    equivalencies.add((key, value))

                for j in range(i + 1, len(foreign_key_dict[key])):
                    equivalencies.add((value, foreign_key_dict[key][j]))

        for col_ind1, col_ind2 in equivalencies:
            col1 = db['column_names_original'][col_ind1][1]
            col2 = db['column_names_original'][col_ind2][1]
            table1 = db['table_names_original'][db['column_names_original'][col_ind1][0]]
            table2 = db['table_names_original'][db['column_names_original'][col_ind2][0]]
            schema['links'][table1][table2] = col1
            schema['links'][table2][table1] = col2

        with open(f'{directory}/{db["db_id"]}.schema', 'w') as out_file:
            json.dump(schema, out_file, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='schema_generate.py')

    parser.add_argument('-schema', required=True, help='spider schema input file "tables.json"')
    parser.add_argument('-out_dir', default=".", help='location of output schema directory')

    parameters = parser.parse_args()

    generate_schema_files(parameters.schema, parameters.out_dir)
