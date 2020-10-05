# coding=utf-8
"""
Query Class
"""
import glob
import logging
import random
import re
from copy import deepcopy, copy
from itertools import product
from math import ceil

from nltk import word_tokenize

from db.sqlite_utils import create_connection
from query.canonicaliser import make_canonical
from query.query_utils import tokenize_sql, translate_argmax_min, groupable, tokenize_nl, \
    list_replace, compSuperDict, join_col, create_join_string, funcParticipleDict, argCommandDict, compDict, funcDict, \
    funcCommandDict, SEP, MAIN_ENT

RE_ENT_LETTER = re.compile(re.compile(r'{ENT[a-z]\}'))
RE_ENT_NUMBER = re.compile(r'{ENT[^0-9]\}')
RE_TEMPLATE = re.compile(r'{.*?\}')
RE_NUMERICAL = re.compile(r'\s(<|>|>=|<=)\s+(?!INTEGER|NUMBER|{)\S')

class Query:
    """
    representing a NL/SQL query

    Attributes:
        Namespace parameters: parameters from generation call
        Schema schema: DB schema
        float layer: filtering parameter
        list nl_tokens: tokenized nl query
        list sql_tokens: tokenized sql query
        bool groupable: sql can be used to create a group by template
        str ent: main ent
        list nl_tokens_filled: nl_tokens but with placeholders replaced through literals
        list sql_tokens_filled: sql_tokens but with placeholders replaced through literals
        dict variables: mapping from placeholders to possible literals
    """

    def __init__(self, nl, sql, schema, parameters, layer=1.0):
        """
        create a query object containing nl and sql

        :param str nl: NL query
        :param str sql: SQL query
        :param Schema schema: schema of the corresponding DB
        :param Namespace parameters: parameters of the original generation call
        :param float layer: parameter for filtering
        """
        self.parameters = parameters
        self.schema = schema
        self.layer = layer

        self.nl_tokens = tokenize_nl(nl)
        self.sql_tokens = tokenize_sql(sql)
        self.groupable = groupable(sql)

        self.ent = None
        self.nl_tokens_filled = None
        self.sql_tokens_filled = None
        self.variables = {}

    def get_sql(self, filled=False):
        """
        reconstruct SQL query by joining tokens with spaces

        :param bool filled: include literals/values
        :return Str: SQL query as a String
        """

        if filled:
            return ' '.join(self.sql_tokens_filled)
        else:
            return ' '.join(self.sql_tokens)

    def get_nl(self, filled=False):
        """
        reconstruct natural language query by joining tokens with spaces

        :param bool filled: include literals/values
        :return Str: natural language query as a String
        """

        if filled:
            return ' '.join(self.nl_tokens_filled).replace("_", " ")
        else:
            return ' '.join(self.nl_tokens).replace("_", " ")

    def create_join_placeholder(self):
        """
        Fill table slots through one or two tables, and insert join templates.

        From a query (generated directly from a template pair),
        create new queries by inserting join statements and replacing ENT slots with ENT1 or ENT1 & 2.
        E.g. in a template containing ENT a,b,c,d substitutes all combinations of ENT1 and ENT2,
        representing tables in the DB linked through a foreign key.
        Leaves ENT 1,2,3 etc. intact.
        Modifies 'self' but does not add it to output!

        :return list: a list of queries with JOIN placeholders and ENT$letter replaced
        """

        new_queries = []

        # find all ent slots with a letter
        ent_slots = list({w for w in re.findall(RE_ENT_LETTER, self.get_nl() + " " + self.get_sql())})
        ent_slots.sort()

        main_ent_token = MAIN_ENT + '.{FROM}' if any(('{FROM}' in token for token in self.sql_tokens)) else MAIN_ENT

        # create new queries with join templates, unless requested otherwise in parameters or not enough slots/tables
        if not self.parameters.no_join and len(ent_slots) > 0 and len(self.schema.tables) > 1:

            # all possible combinations of 1 and 2, repetitions based on amount of ENT slots
            cross_products = [i for i in product([1, 2], repeat=len(ent_slots))]

            join_from = f'JOIN_FROM( {MAIN_ENT} {SEP} {{ENT2}} )'
            join_where = f'JOIN_WHERE( {MAIN_ENT} {SEP} {{ENT2}} ) AND'
            where_join_where = f'WHERE JOIN_WHERE( {MAIN_ENT} {SEP} {{ENT2}} )'

            # skip all ENT1 (trivial case after loop), skip all ENT2 to avoid joins over tables not being used otherwise
            for cross_product in cross_products[1:-1]:
                new_query = deepcopy(self)

                for i, ent_slot in enumerate(ent_slots):
                    slot_fill_ent = f'{{ENT{cross_product[i]}}}'
                    list_replace(new_query.nl_tokens, ent_slot, slot_fill_ent, slot_fill_ent)
                    list_replace(new_query.sql_tokens, ent_slot, slot_fill_ent, slot_fill_ent)
                list_replace(new_query.nl_tokens, main_ent_token, MAIN_ENT, MAIN_ENT)

                list_replace(new_query.sql_tokens, main_ent_token, main_ent_token, join_from)

                from_index = new_query.sql_tokens.index('FROM')
                if 'WHERE' in new_query.sql_tokens:  # insert after 'WHERE'
                    new_query.sql_tokens[from_index + 3:from_index + 3] = [join_where]
                else:  # insert after JOIN_FROM
                    new_query.sql_tokens[from_index + 2:from_index + 2] = [where_join_where]

                new_query.sql_tokens = tokenize_sql(new_query.get_sql())

                # artificially boost recursive layer of new templates
                new_query.layer += self.parameters.join_boost + len(ent_slots)

                assert not re.search(RE_ENT_NUMBER, new_query.get_nl()), f'bad ENT slot in NL:{new_query.get_nl()}'
                assert not re.search(RE_ENT_NUMBER, new_query.get_sql()), f'bad ENT slot in SQL:{new_query.get_sql()}'

                new_queries.append(new_query)

        # modify the original query to no longer include other ENT slots than the main ENT
        for ent_slot in ent_slots:
            list_replace(self.nl_tokens, ent_slot, MAIN_ENT, MAIN_ENT)
            list_replace(self.sql_tokens, ent_slot, MAIN_ENT, MAIN_ENT)

        return new_queries

    def create_argmin_max(self):
        """
        Create an argmin/argmax query from a query with a {from} slot

        :return list: list of the original query (FROM slot removed) and (if FROM slot existed) one with argmax/min slot
        """

        from_slot = next((token for token in self.nl_tokens if '{FROM' in token), None)

        if not from_slot:
            return [self]

        new_query = deepcopy(self)

        i = new_query.nl_tokens.index(from_slot)
        new_query.nl_tokens[i] = f'{MAIN_ENT} {{withToken}} the {{ARG1}} {MAIN_ENT}.{{COL2f}}'
        new_query.nl_tokens = tokenize_nl(new_query.get_nl())

        i = new_query.sql_tokens.index(from_slot)
        new_query.sql_tokens[i] = MAIN_ENT
        if len(new_query.sql_tokens) > i + 1:
            new_query.sql_tokens[i + 2:i + 2] = ['{ARG1}', '(', f'{MAIN_ENT}.{{COL2f}}', SEP, MAIN_ENT, SEP]
        else:
            new_query.sql_tokens.extend(['WHERE', '{ARG1}', '(', f'{MAIN_ENT}.{{COL2f}}', SEP, MAIN_ENT, SEP])
        new_query.sql_tokens.append(')')

        assert new_query.get_sql().count('(') == new_query.get_sql().count(
            ')'), f'unbalanced number of parentheses: {new_query.get_sql()}'
        assert ('WHERE' in new_query.get_sql()), f'No WHERE keyword in query: {new_query.get_sql()}'

        new_query.layer += self.parameters.argmax_boost

        list_replace(self.nl_tokens, from_slot, MAIN_ENT, MAIN_ENT)
        list_replace(self.sql_tokens, from_slot, MAIN_ENT, MAIN_ENT)
        self.layer += 1

        return [new_query, self]

    # TODO refactor return
    # TODO use self consistently
    def fill_slots(self, token, slot_fill_dict):
        """
        apply slot-filling dictionary or other slot filling mechanism to the first template slot in the given token

        :param str token: token from the NL query that contains an unfilled slot
        :param dict slot_fill_dict: dictionary that maps slots to possible values for NL queries
        :return list: generated queries
        """

        new_queries = []

        # extract the first template slot (recognized by {})
        slot = re.search(RE_TEMPLATE, token).group(0)

        filter_probability = 1 if self.parameters.no_filter or self.layer < self.parameters.threshold else (
                self.parameters.a + (self.parameters.b / self.layer))

        # options for function slots
        functions = ['max', 'min', 'avg', 'sum']

        # for keys in the slot-filling dictionary
        if slot in slot_fill_dict:

            number_of_samples = int(ceil(len(slot_fill_dict[slot]) * filter_probability))
            for i, value in enumerate(random.sample(slot_fill_dict[slot], number_of_samples)):
                new_query = deepcopy(self) if i < (number_of_samples - 1) else self
                list_replace(new_query.nl_tokens, slot, value, value)
                list_replace(new_query.sql_tokens, slot, value.upper(), value.upper())

                new_query.layer += 1

                new_queries.append(new_query)

        # for slots representing SQL tables
        elif '{ENT' in slot:

            tables = [key for key in self.schema.tables.keys() if
                      key not in self.sql_tokens]  # no aggregation over one table
            number_of_samples = int(ceil(len(tables) * filter_probability))
            for i, ent in enumerate(random.sample(tables, number_of_samples)):

                new_query = deepcopy(self) if i < number_of_samples - 1 else self

                list_replace(new_query.nl_tokens, slot, ent, self.schema.defaults[ent]['utt'])
                list_replace(new_query.sql_tokens, slot, ent, ent)

                if not new_query.ent:
                    new_query.ent = ent

                new_query.layer += 1

                new_queries.append(new_query)

        # for slots representing columns
        elif '{COL' in slot:

            ent = token.split('.')[0]

            # postpone until table name was filled in
            if "{" in ent:
                return [self]

            tables = self.schema.tables[ent]
            number_of_samples = int(ceil(len(tables) * filter_probability))
            for i, column in enumerate(random.sample(list(tables), number_of_samples)):

                # fill those ending in f only if number type column
                if slot[-2] != 'f' or tables[column]['type'] in ['INTEGER', 'NUMBER']:

                    new_query = deepcopy(self) if i < number_of_samples - 1 else self

                    list_replace(new_query.nl_tokens, f'{ent}.{slot}', f'{ent}.{column}', tables[column]['utt'])
                    list_replace(new_query.sql_tokens, f'{ent}.{slot}', f'{ent}.{column}', f'{ent}.{column}')

                    new_query.layer += 1

                    digit = slot[slot.find('{COL') + 4: -1]

                    comp_slot = f'{{COMP{digit}}}'
                    # to avoid unnecessary string comparison
                    if tables[column]['type'] in ['INTEGER', 'NUMBER'] or comp_slot not in new_query.nl_tokens:
                        new_queries.append(new_query)

                    else:
                        # to avoid overpopulating '!=' tokens for numerical columns
                        if random.random() < self.parameters.unequal_p:
                            comparison = '!='
                            query_unequal = deepcopy(new_query)
                            list_replace(query_unequal.nl_tokens, comp_slot, compDict[comparison], compDict[comparison])
                            list_replace(query_unequal.sql_tokens, comp_slot, comparison, comparison)

                            query_unequal.layer += 1

                            new_queries.append(query_unequal)

                        comparison = '='
                        list_replace(new_query.nl_tokens, comp_slot, compDict[comparison], compDict[comparison])
                        list_replace(new_query.sql_tokens, comp_slot, comparison, comparison)

                        new_query.layer += 1

                        new_queries.append(new_query)

            return new_queries

        # for slots representing literals/values
        elif '{LITERAL' in slot:

            ent = token.split('.')[0]
            column = token.split('.')[1]

            if self.parameters.fill_literals:
                default_value = f'{ent}.{column}.{self.schema.tables[ent][column]["type"]}@{token[-2]}'
            else:
                default_value = f'{self.schema.tables[ent][column]["type"]}@{token[-2]}'

            list_replace(self.nl_tokens, f'{ent}.{column}.{slot}', default_value, default_value)
            list_replace(self.sql_tokens, f'{ent}.{column}.{slot}', default_value, default_value)

            self.layer += 1

            # drop all queries that do numerical comparisons on columns with non-numerical values
            if not re.search(RE_NUMERICAL, self.get_sql()):
                new_queries.append(self)

            return new_queries

        # for slots meant to be filled with columns/tables of the same type as another
        elif '{MATCHFILL' in slot:

            split_token = token.split(".")

            # do other MATCHFILL tokens instead
            if len(split_token) == 1 or '{' in split_token[0]:
                return [self]

            ent = split_token[0]
            column = split_token[1]

            columns = list(self.schema.type_dict[self.schema.tables[ent][column]['type']])
            for new_column, new_ent in random.sample(columns,
                                                     min(int(ceil(self.parameters.in_boost * filter_probability)),
                                                         len(columns))):

                # exclude original table column combination
                if new_column == column and new_ent == ent:
                    continue

                new_query = deepcopy(self)

                # replace MATCHFILL token
                list_replace(new_query.nl_tokens, f'{ent}.{column}.{{MATCHFILL{slot[-2]}}}', f'{new_ent}.{new_column}',
                             self.schema.tables[new_ent][new_column]['utt'])
                list_replace(new_query.sql_tokens, f'{ent}.{column}.{slot}', f'{new_ent}.{new_column}',
                             f'{new_ent}.{new_column}')

                # replace MATCHFILLTABLE token
                list_replace(new_query.nl_tokens, f'{{MATCHFILLTABLE{slot[-2]}}}', new_ent,
                             self.schema.defaults[new_ent]['utt'])
                list_replace(new_query.sql_tokens, f'{{MATCHFILLTABLE{slot[-2]}}}', new_ent, new_ent)

                new_query.layer += self.parameters.in_boost

                new_queries.append(new_query)

            return new_queries

        # for slots representing the default column of a table
        elif '{DEF' in slot:

            ent = token.split('.')[0]

            default_col = self.schema.defaults[ent]['col']

            list_replace(self.nl_tokens, f'{ent}.{slot}', '', '')
            list_replace(self.sql_tokens, f'{ent}.{slot}', f'{ent}.{default_col}', f'{ent}.{default_col}')

            self.layer += 1

            new_queries.append(self)

        # for slots representing relational operators/comparisons
        elif '{COMP' in slot:

            digit = slot[-1]
            matching_column = '{COL' + digit + '}'
            if matching_column in self.nl_tokens:
                new_queries.append(self)
            else:
                operators = ['=', '!=', '<', '>', '<=', '>=']
                for comparison in random.sample(operators, int(ceil(len(operators) * filter_probability))):
                    new_query = deepcopy(self)

                    list_replace(new_query.nl_tokens, slot, compDict[comparison], compDict[comparison])
                    list_replace(new_query.sql_tokens, slot, comparison, comparison)

                    new_query.layer += 1

                    new_queries.append(new_query)

        # for slots representing functions
        elif '{FUNC' in slot:

            for function in random.sample(functions, int(ceil(len(functions) * filter_probability))):
                new_query = deepcopy(self)

                list_replace(new_query.nl_tokens, slot, funcDict[function], funcDict[function])
                list_replace(new_query.sql_tokens, slot, function, function)

                new_query.layer += self.parameters.func_boost

                new_queries.append(new_query)

        # for slots representing function commands
        elif '{funcCommand' in slot:

            for function in random.sample(functions, int(ceil(len(functions) * filter_probability))):
                new_query = deepcopy(self)

                list_replace(new_query.nl_tokens, slot, funcCommandDict[function], funcCommandDict[function])
                list_replace(new_query.sql_tokens, slot, function, function)

                new_query.layer += 1

                new_queries.append(new_query)

        # for slots representing function participles
        elif '{funcParticiple' in slot:

            for function in random.sample(functions, int(ceil(len(functions) * filter_probability))):
                new_query = deepcopy(self)

                list_replace(new_query.nl_tokens, slot, funcParticipleDict[function], funcParticipleDict[function])
                list_replace(new_query.sql_tokens, slot, function, function)

                new_query.layer += 1

                new_queries.append(new_query)

        # for slots representing argmax/argmin
        elif '{ARG' in slot:

            arg_functions = ['argmax', 'argmin']
            for minmax in random.sample(arg_functions, int(ceil(len(arg_functions) * filter_probability))):
                new_query = deepcopy(self)

                list_replace(new_query.nl_tokens, slot, argCommandDict[minmax], argCommandDict[minmax])
                list_replace(new_query.sql_tokens, slot, minmax, minmax)

                new_query.layer += 1

                new_queries.append(new_query)

        # for adjective slots
        # TODO adjust by partly moving to paraphrasing
        elif slot in {'{greatToken}', '{smallToken}'}:

            number_of_samples = int(ceil(self.parameters.adjective_scale * filter_probability))

            for i, adjective in enumerate(random.sample(compSuperDict[slot], number_of_samples)):
                new_query = deepcopy(self) if i < number_of_samples - 1 else self

                list_replace(new_query.nl_tokens, slot, adjective, adjective)

                new_query.layer += 1

                new_queries.append(new_query)

        # for slots being filled with comparative/superlative forms of adjectives
        elif slot in compSuperDict:

            comparative_superlative = random.choice(compSuperDict[slot])

            list_replace(self.nl_tokens, slot, comparative_superlative, comparative_superlative)

            self.layer += 1

            new_queries.append(self)

        # for slots representing 'and' or 'or'
        elif '{andOrToken' in slot:

            words = ['and', 'or'] if random.random() < self.parameters.or_p else ['and']

            for value in words:
                new_query = deepcopy(self)

                list_replace(new_query.nl_tokens, slot, value, value)
                list_replace(new_query.sql_tokens, slot, value.upper(), value.upper())

                new_query.layer += 1

                new_queries.append(new_query)

        else:
            logging.warning(f'template slot {slot} not recognized for {self.get_nl()}')
            return []

        if len(new_queries) == 0:
            return [self]

        return new_queries

    def translate_max_count(self):
        """ translate COUNT_COND in SQL query to construct with JOIN, GROUP BY, ORDER BY
        """

        try:
            i = self.sql_tokens.index('COUNT_COND')
        except ValueError:
            return True  # no COUNT_COND in the SQL query

        table_1 = self.sql_tokens[i + 2]
        table_2 = self.sql_tokens[i + 4]

        if table_2 == table_1:
            logging.warning('dropped query with aggregation over one table')
            return False  # improper configuration of tables in COUNT_COND, ignore query

        cond = []
        cond_start = i + 6  # assuming minimal form COUNT_COND ( {ENT$} $ {ENT$} $ ) , point to closing parenthesis
        idx_counter = 0
        while self.sql_tokens[cond_start + idx_counter] != ")":
            cond += [self.sql_tokens[cond_start + idx_counter]]
            idx_counter += 1

        join_where = create_join_string(table_2, table_1, self.schema, 'JOIN_WHERE')

        if join_where is None:
            logging.info(f'no join path found between {table_1} and {table_2}')
            return False

        if join_where.count(' = ') > 1:
            logging.info(f'need recursive JOIN for: {join_where}')
            return False  # TODO adapt when longer paths are implemented

        join_1, join_2 = join_where.split(' = ')

        new_sql = self.sql_tokens[0:i] + [join_1, "= ( SELECT", join_2, "FROM", table_1]
        if cond:
            new_sql += ['WHERE'] + cond
        new_sql += ["GROUP BY", join_2, "ORDER BY count ( * ) desc limit 1"]
        new_sql += self.sql_tokens[cond_start + idx_counter:]

        self.sql_tokens = new_sql

        return self.translate_max_count()

    def fill_in_join_cols(self):
        """
        resolve JOIN_COL by creating a Join over tables linked through a foreign key

        :return bool: whether JOIN could be created
        """

        new_sql = []
        i = 0
        while i < len(self.sql_tokens):
            if self.sql_tokens[i] == 'JOIN_COL':

                ent1 = self.sql_tokens[i + 2]
                ent2 = self.sql_tokens[i + 4]

                join = join_col(ent1, ent2, self.schema)

                if not join:
                    return False

                new_sql.append(join)
                i += 5

            else:
                new_sql.append(self.sql_tokens[i])

            i += 1

        self.sql_tokens = new_sql

        return True

    def fill_in_joins(self):
        """

        :return:
        """

        i = 0
        new_sql = []
        while i < len(self.sql_tokens):

            if self.sql_tokens[i] in ['JOIN_WHERE', 'JOIN_FROM']:

                table1 = self.sql_tokens[i + 2]
                table2 = self.sql_tokens[i + 4]

                join = create_join_string(table1, table2, self.schema, self.sql_tokens[i])

                if join is None:
                    return False

                new_sql.append(join)

                i += 5
                if join == '':
                    if len(self.sql_tokens) > i + 1 and self.sql_tokens[i + 1] == 'AND':
                        i += 2
                        new_sql[-1] = self.sql_tokens[i]
                    else:
                        new_sql[-2:] = self.sql_tokens[i + 1:i + 3]
                        i += 2
            else:
                new_sql.append(self.sql_tokens[i])

            i += 1

        self.sql_tokens = new_sql
        return True

    def replace_values(self, database):
        """ replace literals placeholders in query with values from the database

        :param database:
        """

        self.nl_tokens_filled = copy(self.nl_tokens)
        self.sql_tokens_filled = copy(self.sql_tokens)
        self.variables = {}

        for i, token in enumerate(self.sql_tokens_filled):
            if '@' in token:
                [ent, col, _] = token.split('.')
                try:
                    literal = str(random.sample(database.literals[(ent, col)], k=1)[0]).split('(')[0]
                except ValueError:
                    logging.error('database is empty while attempting to fill literals')
                    return False

                placeholder = 'var' + token[-1]
                list_replace(self.sql_tokens, token, f'\"{placeholder}\"', f'\"{placeholder}\"')
                list_replace(self.sql_tokens_filled, token, f'\"{literal}\"', f'\"{literal}\"')
                list_replace(self.nl_tokens_filled, token, literal, literal)
                list_replace(self.nl_tokens, token, placeholder, placeholder)
                self.variables[placeholder] = literal

        for i, word in enumerate(self.nl_tokens):
            if '@' in word:
                [ent, col, _] = word.split('.')
                literal = str(random.sample(database.literals[(ent, col)], k=1)[0])
                list_replace(self.nl_tokens_filled, word, literal, standalone=literal)

        assert '@' not in self.get_nl(), f'found @ in NL after replacing values : {self.get_nl()}'

        return True

    def valid(self):
        """ Check whether query can be executed, validating against DB

        :return bool: whether the query is valid on this DB
        """

        sql = self.get_sql()
        for type_string in sorted(self.schema.types, key=len, reverse=True):
            sql = re.sub(f'{type_string}@\\d+', r'"placeholder"', sql)

        # try to run sql
        db_path = glob.glob(self.parameters.db_dir + '/*.sqlite')[0]
        db_conn = create_connection(db_path)
        if not db_conn:
            logging.error('error while connecting to sqlite DB')
        else:
            logging.debug(f'executing query: {sql}')
            with db_conn:
                cursor = db_conn.cursor()
                try:
                    cursor.execute(sql)
                except Exception as e:
                    logging.error(f'ERROR: {self.get_nl()} {SEP} {sql} {e}')
                    return False
        return True

    def output_paraphrases(self, paraphraser, database, data, json_data):
        """
        create NL paraphrases and output samples to provided data structures

        :param paraphraser: PPDB paraphraser
        :param database: associated database object
        :param data: list for samples
        :param json_data: list for json formatted samples
        """

        sql = self.get_sql()
        if self.parameters.fill_literals:
            sql = self.get_sql(filled=True)
            paraphrases = paraphraser.get_paraphrases(self.nl_tokens_filled)
        else:
            paraphrases = paraphraser.get_paraphrases(self.nl_tokens)
        if not self.parameters.no_canonical:
            sql = make_canonical(sql, database.umich_schema, self.variables)

        for type_string in sorted(self.schema.types, key=len, reverse=True):
            sql = re.sub(f'{type_string}@\\d+', r'"value"', sql)
        sql_label = sql.replace("'", '')

        try:
            sql_label = database.parse_query(sql_label)
        except AssertionError:
            logging.error(f'could not create SQL label for {sql_label}')
            print(f'could not create SQL label for {sql_label}')
            return

        sql_no_values = sql
        for value in self.variables.values():
            sql_no_values = sql_no_values.replace(value, 'value')
        sql_no_values = sql_no_values.replace('"value"', 'value')
        sql_no_values = sql_no_values.replace('10', 'value')

        for p in paraphrases:

            for type_string in sorted(self.schema.types, key=len, reverse=True):
                p = re.sub(f'{type_string}@\\d+', r'value', p)

            data.append((p, sql))

            json_item = {'db_id': self.parameters.db,
                         'query': sql,
                         'query_no_value': sql_no_values,
                         'query_toks': word_tokenize(sql),
                         'query_toks_no_value': word_tokenize(sql_no_values),
                         'question': p,
                         'question_toks': word_tokenize(p),
                         'sql': sql_label,
                         'variables': self.variables}
            json_data.append(json_item)

    def output(self, paraphraser, database, data, json_data):
        """ post-processes and outputs query in which all slots have been filled

        :param paraphraser: PPDB paraphraser
        :param database: associated database object
        :param data: list for output data
        :param json_data: dict for json formatted output data
        """

        nl = self.get_nl()
        sql = self.get_sql()

        assert '{' not in nl, 'attempting to output ill-constructed query; { in nl query'
        assert '{' not in sql, 'attempting to output ill-constructed query; { in sql query'

        assert nl.count('(') == nl.count(')'), f'uneven parentheses in NL query: {nl}'
        assert sql.count('(') == sql.count(')'), f'uneven parentheses in SQL query: {sql}'

        if not self.translate_max_count():
            return

        if not self.fill_in_join_cols():
            return

        if not self.fill_in_joins():
            return

        self.sql_tokens = translate_argmax_min(self.get_sql()).split()

        if self.parameters.fill_literals:
            if not self.replace_values(database):
                logging.warning('could not fill literals, aborting output')
                return

        if self.parameters.validate:
            if not self.valid():
                logging.warning("invalid query, aborting output")
                return

        self.output_paraphrases(paraphraser, database, data, json_data)

    def __str__(self):
        return self.get_sql()

    def __deepcopy__(self, memo):
        """
        custom deepcopy method; starting from a shallow copy
        leave immutable attributes (strings, numbers)
        leave references to those, that do not differ for queries on the same DB (Database, Schema)
        copy dicts/lists that change for each query (shallow copy since they contain strings)

        :param memo: list of copied objects
        :return Query: copied Query object
        """
        new = copy(self)

        new.nl_tokens = copy(self.nl_tokens)
        new.sql_tokens = copy(self.sql_tokens)
        new.nl_tokens_filled = copy(self.nl_tokens_filled)
        new.sql_tokens_filled = copy(self.sql_tokens_filled)

        new.variables = copy(self.variables)

        return new
