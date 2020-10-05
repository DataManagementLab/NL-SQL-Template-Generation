#!/usr/bin/env python3
"""
Synthetic Data Generation for NL to SQL translation in Databases.

Call this file to start data generation, db parameter is obligatory.
See help strings below for further parameters.
"""

import argparse
import logging
import random
from time import strftime

import numpy as np

from generation.generator import Generator


def generation_parameters():
    """
    create generation ArgumentParser and process given parameters

    :return Namespace: arguments parsed by ArgumentParser
    """

    parser = argparse.ArgumentParser(description='Initiate Data Generation Pipeline')

    parser.add_argument('-db', help='database name (required)', required=True)

    # file/directory arguments
    parser.add_argument('-db_dir', help='database directory, defaults to data/spider/database/<db>')
    parser.add_argument('-schema', help='path to schema file; defaults to data/spider/schemas/<db>/<db>.schema ')
    parser.add_argument('-json_schema', default='data/spider/tables.json', help='path to json file with db schema info')
    parser.add_argument('-dict', default='data/slot_filling_dict.txt', help='slot filling dictionary of synonyms')
    parser.add_argument('-templates', default='data/templates.txt', help='file containing NL/SQL templates')
    parser.add_argument('-ppdb_file', default='data/ppdb/ppdb.json', help='PPDB file for paraphrasing')
    parser.add_argument('-out_dir', help='output directory; if not specified, defaults to data/spider/synthetic/<db>/')

    # Logging arguments
    parser.add_argument('-verbose', action='store_true', help='log low importance info, progress and debugging info')
    parser.add_argument('-log', default=f'logs/{strftime("%Y%m%d-%H%M%S")}.log', help='specify log file')

    # generation pipeline modifiers
    parser.add_argument('-toy', action='store_true', help='activate toy mode for faster execution, meant for debugging')
    parser.add_argument('-validation_split', type=float, default=0.0, help='size of validation set, defaults to 0')
    parser.add_argument('-no_group_by', action='store_true', help='no additional GROUP BY queries, ignore group_by_p')
    parser.add_argument('-no_join', action='store_true', help='generate no JOIN queries')
    parser.add_argument('-no_filter', action='store_true', help='do not prune slot filling recursion tree')
    parser.add_argument('-no_canonical', action='store_true', help='do not canonicalize sql queries')
    parser.add_argument('-validate', action='store_true', help='validate generated queries with sqlite database')
    parser.add_argument('-fill_literals', action='store_true', help='fill literal placeholders with values from DB')

    # slot filling parameters
    parser.add_argument('-group_by_p', type=float, default=0.292, help='P(GROUP BY template from oen with aggregation)')
    parser.add_argument('-a', type=float, default=.081, help='pruning parameter: P(keep)=a+(b/layer)')
    parser.add_argument('-b', type=float, default=.767, help='pruning parameter: P(keep)=a+(b/layer)')
    parser.add_argument('-func_boost', type=int, default=3, help='function layer boost (higher=less function queries)')
    parser.add_argument('-argmax_boost', type=int, default=3, help='argmax query slot-filling layer boost')
    parser.add_argument('-join_boost', type=int, default=2, help='join query slot-filling layer boost')
    parser.add_argument('-in_boost', type=int, default=3, help='in query slot-filling layer boost')
    parser.add_argument('-threshold', type=int, default=6, help='recursive level to start filtering')
    parser.add_argument('-query_bound', type=int, default=5000, help='loose bound on queries generated per template')
    parser.add_argument('-unequal_p', type=int, default=0.2, help='probability for creating unequal comparisons')
    parser.add_argument('-or_p', type=int, default=0.2, help='probability with which to create or statements')

    # augmentation parameters
    parser.add_argument('-pp_scale', type=int, default=0, help='Number of paraphrases through token substitution')
    parser.add_argument('-rand_drop_p', type=float, default=.875, help='random word drop probability')
    parser.add_argument('-rand_drop_scale', type=int, default=0, help='random word drop scale; no. tokens per NL query')
    parser.add_argument('-adjective_scale', type=int, default=3, help='number of adjectives used per template slot')

    params = parser.parse_args()

    # default values and dependent parameters not handled by ArgumentParser

    # set default value for data base directory dependent on db
    if not params.db_dir:
        params.db_dir = f'data/spider/database/{params.db}'
    # set default value for schema file dependent on db parameter
    if not params.schema:
        params.schema = f'data/spider/schemas/{params.db}/{params.db}.schema'
    # set default value for output directory dependent on db parameter
    if not params.out_dir:
        params.out_dir = f'data/spider/synthetic/{params.db}/'
    # add trailing slash on output directory if necessary
    if params.out_dir[-1] != '/':
        params.out_dir += '/'
    # set p to zero if group_by is disabled
    if params.no_group_by:
        params.group_by_p = 0

    # toy mode
    if params.toy:
        params.query_bound = 5
        params.threshold = 3
        params.verbose = True
    return params


if __name__ == '__main__':
    """set up argument parser, process arguments and call generate method
    """

    # seed sources of randomness to be able to reproduce results
    random.seed(42)
    np.random.seed(42)

    # retrieve and process parameters
    parameters = generation_parameters()

    # setup logging
    if parameters.verbose:
        logging.basicConfig(filename=parameters.log, level=logging.DEBUG)
    else:
        logging.basicConfig(filename=parameters.log, level=logging.WARNING)

    if parameters.toy:
        logging.warning('toy mode active')

    # start training data generator
    generator = Generator(parameters)
    generator.generate_from_input()
    generator.output_samples()
