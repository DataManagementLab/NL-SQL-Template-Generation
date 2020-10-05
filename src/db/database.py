# coding=utf-8
""" Database class
"""
import glob
import json
import logging

from db.sqlite_utils import get_literals
from spider import process_sql
from spider.parse_raw_json import get_schemas_from_json, Schema as SpiderSchema


class Database:
    """ class representing a Database

    Attributes:
        name: name of the DB
        directory: location of sqlite file
        schema: DB schema
        tables_file: location of the spider tables.json file
        sqlite: location of the sqlite file
        literals: values that occur in the DB
        spider_schema:
        umich_schema:
    """

    def __init__(self, db, db_directory, schema, tables_file):
        self.name = db
        self.directory = db_directory
        self.schema = schema
        self.tables_file = tables_file

        db_files = glob.glob(self.directory + '/*.sqlite')
        assert db_files, f'no sqlite files in {self.directory} for db {self.name}.'
        assert len(db_files) == 1, f'multiple sqlite files in {self.directory} for db {self.name}.'

        self.sqlite = db_files[0]

        self.literals = self.get_column_values()
        schemas, db_names, tables = get_schemas_from_json(self.tables_file)
        self.spider_schema = SpiderSchema(schemas[self.name], tables[self.name])
        self.umich_schema = self.make_umich()

    def get_column_values(self):
        """
        retrieve values occurring in the DB

        None if no schema provided

        :return dict: dictionary associating each tuple af ent and column with values
        """
        if not self.schema:
            logging.warning('no schema to generate literals from column values')
            return None

        value_dict = {}
        for table in self.schema.tables:
            for column in self.schema.tables[table]:
                value_dict[(table, column)] = get_literals(self.sqlite, [(table, column)])

        if not any((bool(value_dict[key]) for key in value_dict)):
            logging.warning(f'no values found in db {self.name}')

        return value_dict

    def make_umich(self):
        """
        create schema for canonicalisation

        :return tuple: dict of all fields of a table, set of all names of tables and fields
        """

        with open(self.tables_file) as open_file:
            schema_info = json.load(open_file)

        db = next((i for i in schema_info if i['db_id'] == self.name))
        all_words = set()
        table_field_map = {}

        for column in db['column_names']:
            table = '_'.join(db['table_names'][column[0]].split()).upper()
            field = '_'.join(column[1].split()).upper()

            if field == '*':
                continue

            table_field_map.setdefault(table, set()).add(field)
            all_words.add(table)
            all_words.add(field)

        return table_field_map, all_words

    def parse_query(self, sql):
        """ parse SQL query according to spider format

        :param str sql: complete sql query as a string
        :return dict: processed sql
        """
        return process_sql.get_sql(self.spider_schema, sql)
