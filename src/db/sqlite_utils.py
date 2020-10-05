# coding=utf-8
""" database utils for using sqlite

"""
import logging
import sqlite3


def create_connection(db_file):
    """ create a database connection to the SQLite database specified by the db_file

    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        conn.text_factory = str
        logging.info('connection made to {}'.format(db_file))
        return conn
    except sqlite3.Error as e:
        logging.error(e)
        return None


def get_literals(db_sqlite, columns):
    """
    Query all rows in the tasks table

    :return:
    """

    conn = create_connection(db_sqlite)
    with conn:
        literals = set()
        for table, col in columns:
            cur = conn.cursor()
            query = f'SELECT "{col}" FROM "{table}"'
            cur.execute(query)
            try:
                rows = cur.fetchall()
            except Exception:
                return None
            for row in rows:
                literals.add(row[0])
    return literals
