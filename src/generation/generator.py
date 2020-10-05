# coding=utf-8
""" synthetic data generator class
"""

import json
import logging
import os
import random
from copy import deepcopy

from db.database import Database
from db.schema import Schema
from generation.generator_utils import read_lines_from_file, parse_dict
from paraphrasing.ppdb import PPDB
from query.query import Query
from query.query_utils import tokenize_nl, tokenize_sql


class Generator(object):
    """
    A generator of synthetic training data for NL to SQL translation.

    Attributes:
        Namespace parameters: a namespace containing all generation parameters; for documentation see generate.py
        dict slot_filling_dictionary: a dictionary containing word groups for slot-filling in natural language queries
        list templates: list of templates for NL/SQL query pairs
        PPDB paraphraser: Paraphraser for creating alternate formulations of NL queries
        Schema schema: database schema
        Database database: representing the database to work on
        list json_samples: list of samples for json output
        list json_validation_samples: list of samples in validation split for json output
        list training_data_split: training split of the generated data
        list validation_data_split: validation split (if requested in parameters) of the generated data
    """

    def __init__(self, parameters):
        """
        initiate Generator and load necessary input from files

        :param Namespace parameters: Namespace containing script arguments
        """

        self.parameters = parameters

        # generated data samples
        self.training_data_split = []
        self.validation_data_split = []
        self.json_samples = []
        self.json_validation_samples = []

        # retrieve templates and slot-filling dictionary
        self.templates = read_lines_from_file(self.parameters.templates)
        self.slot_filling_dictionary = parse_dict(self.parameters.dict)

        # Instantiate paraphraser, schema, and database
        self.schema = Schema(self.parameters.schema)
        self.database = Database(self.parameters.db,
                                 self.parameters.db_dir,
                                 self.schema,
                                 self.parameters.json_schema)
        self.paraphraser = PPDB(self.parameters.ppdb_file,
                                self.parameters.pp_scale,
                                self.parameters.rand_drop_scale,
                                self.parameters.rand_drop_p)

    def generate(self, query, samples):
        """
        recursive generation of examples by substituting one at a time

        :param Query query: current query
        :param list samples: previously generated samples for this query
        """

        # limit per-template sample production
        if len(samples) >= self.parameters.query_bound:
            return

        # substitute one random template tag and recursively call method again
        found_template_tag = False
        for token in random.sample(query.nl_tokens, len(query.nl_tokens)):
            if '{' in token:  # is a template slot
                queries = query.fill_slots(token, self.slot_filling_dictionary)
                for new_query in queries:
                    try:
                        self.generate(new_query, samples)
                    except RecursionError:
                        logging.error(f'recursion depth exceeded in {new_query}')

                found_template_tag = True
                # only substitute one template tag at a time
                break

        # none of the current tokens is a template tag
        if not found_template_tag:

            query.output(self.paraphraser, self.database, samples, self.json_samples)

            # TODO move?
            # generate additional group by queries
            if random.random() < self.parameters.group_by_p and query.groupable:
                new_nl = f'{{groupByToken}} {query.ent}.{{COL4}} {query.get_nl()}'
                new_sql = f'SELECT {query.ent}.{{COL4}} ,{query.get_sql()[7:]} GROUP BY {query.ent}.{{COL4}}'
                new_query = deepcopy(query)

                new_query.nl_tokens = tokenize_nl(new_nl)
                new_query.sql_tokens = tokenize_sql(new_sql)
                new_query.groupable = False

                self.generate(new_query, samples)

    def generate_from_input(self):
        """ generate training data from templates and a slot filling dictionary
        """

        logging.info(f'generating from dictionary {self.parameters.dict} and template file {self.parameters.templates}')

        sample_count = 0
        self.training_data_split = []

        for line in self.templates:

            previous_count = sample_count

            query_templates = line.split('\t')
            sql_template = query_templates.pop()

            for nl_template in query_templates:

                original_query = Query(nl_template, sql_template, self.schema, self.parameters)
                logging.debug(f'generating NL from: {original_query.get_nl()}')

                # generate query for  every combination of linked tables in multi-table queries
                queries = original_query.create_join_placeholder()
                # create argmin/argmax queries
                queries += original_query.create_argmin_max()

                for query in queries:
                    samples = []
                    self.generate(query, samples)
                    self.training_data_split.extend(samples)

                    new_sample_count = len(self.training_data_split)
                    logging.info(f'count: {new_sample_count - sample_count} out of total: {new_sample_count}')
                    sample_count = new_sample_count

            logging.info(f'total count for template: {sample_count - previous_count}')

        former_size = len(self.training_data_split)
        logging.info(f'total count generated from all templates: {former_size}')

        # remove duplicate queries
        self.training_data_split = list(set(self.training_data_split))
        self.training_data_split.sort()

        logging.info(f'removed {former_size - len(self.training_data_split)} duplicates')
        nl = len({nl for (nl, sql) in self.training_data_split})
        sql = len({sql for (nl, sql) in self.training_data_split})
        logging.info(f'{nl} unique NL queries')
        logging.info(f'{sql} unique SQL queries')
        try:
            logging.info(f'{nl / sql} paraphrases on average for each SQL query')
        except:
            pass  # paraphrasing deactivated?

    def output_samples(self):
        """
        output generated samples to files

        Creates one file with nl training data and one file with SQL training data.
        If requested, creates nl and sql files for validation data split.
        """

        assert self.training_data_split, 'need to generate data by calling generate_from_input before output'

        out_path = self.parameters.out_dir + self.parameters.db
        if not os.path.exists(self.parameters.out_dir):
            os.makedirs(self.parameters.out_dir)

        logging.info(f'Begin writing to {self.parameters.out_dir}*')

        # if validation data set was requested: split off specified percentage randomly
        if self.parameters.validation_split:

            random.shuffle(self.training_data_split)

            split_point = int(self.parameters.validation_split * len(self.training_data_split))
            self.validation_data_split = self.training_data_split[:split_point]
            self.training_data_split = self.training_data_split[split_point:]

            with open(out_path + '_val.nl', 'w') as v_nl, open(out_path + '_val.sql', 'w') as v_sql:
                for (n, s) in self.validation_data_split:
                    v_nl.write(n + '\n')
                    v_sql.write(s + '\n')

        # write (remaining) samples to training data files
        with open(out_path + '_train.nl', 'w') as t_nl, open(out_path + '_train.sql', 'w') as t_sql:
            for (n, s) in self.training_data_split:
                t_nl.write(n + '\n')
                t_sql.write(s + '\n')

        # json format data samples

        # if validation data set was requested: split off specified percentage randomly
        if self.parameters.validation_split:
            random.shuffle(self.json_samples)

            split_point = int(self.parameters.validation_split * len(self.json_samples))
            self.json_validation_samples = self.json_samples[:split_point]
            self.json_samples = self.json_samples[split_point:]

            with open(self.parameters.out_dir + 'dev.json', 'w') as v_json:
                json.dump(self.json_validation_samples, v_json, sort_keys=True, indent=4, separators=(',', ': '))

        # write (remaining) samples to training data files
        with open(self.parameters.out_dir + 'train.json', 'w') as t_json:
            json.dump(self.json_samples, t_json, sort_keys=True, indent=4, separators=(',', ': '))

        logging.info('Finished output!')
