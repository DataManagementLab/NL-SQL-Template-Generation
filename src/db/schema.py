# coding=utf-8
""" Schema class
"""
from collections import OrderedDict

import commentjson


class Schema:
    """
    class representing a DB scheme
    read from .schema file, refer to helper_scripts/schema_generate.py

    Attributes:
        schema: Schema as read from the file
        tables: tables with attributes of the DB
        types: all attribute types of the DB
        defaults: default table and column names for original table names
        links: links between tables
        type_dict: dictionary of types
    """

    def __init__(self, filename):
        self.schema = commentjson.loads(open(filename).read())

        # for convenience
        self.tables = self.schema['ents']
        self.types = self.schema['types']
        self.defaults = self.schema['defaults']
        if 'links' in self.schema:
            self.links = self.schema['links']
        self.type_dict = OrderedDict([(typ, [item for sublist in
                                             [[(col, ent) for col in self.tables[ent] if
                                               self.tables[ent][col]['type'] == typ] for ent
                                              in self.tables] for item in sublist]) for typ in self.types])
