# coding=utf-8
"""
utility methods for handling queries
"""
import logging
import os
import pickle
import re

compDict = {'=': '{logicToken.equalToken}', '!=': '{logicToken.notEqualToken}',
            '>': '{logicToken.strictlyGreaterToken}', '<': '{logicToken.strictlySmallerToken}',
            '>=': '{logicToken.greaterToken}', '<=': '{logicToken.smallerToken}'}
funcDict = {'max': '{functionToken.maxToken}', 'min': '{functionToken.minToken}', 'avg': '{functionToken.avgToken}',
            'sum': '{functionToken.sumToken}'}
funcCommandDict = {'max': 'maximize', 'min': 'minimize', 'avg': 'average', 'sum': 'summate'}
funcParticipleDict = {'max': 'maximizing', 'min': 'minimizing', 'avg': 'averaging', 'sum': 'summating'}
argCommandDict = {'argmax': '{functionToken.maxToken}', 'argmin': '{functionToken.minToken}'}

compSuperDict = pickle.load(open('../data/compsupadj.pickle', 'rb')) if 'data' not in os.listdir('.') else pickle.load(
    open('data/compsupadj.pickle', 'rb'))

RE_ARG = re.compile(r'argmin \(|argmax \(')
RE_SPECIAL_CHAR_SPACE = re.compile(r'([,!?()])')
RE_APOSTROPHE = re.compile(r"'([a-zA-Z]+)\s")
RE_FULL_STOP = re.compile(r'\.[$\s]')
RE_SPECIAL_CHAR = re.compile(r'([\\,!?;+*<>()=/-])')
RE_SQL_SPACE = re.compile(r'([<>!])\s+([=])')
SIMPLIFY_SQL = [(re.compile(r'count(\s)*\((\s*)1(\s*)\)'), r'count'),
                (re.compile(r'(argmax|argmin|max|min|avg|sum|in|IN)\s\('), r'\1('),
                (re.compile(r'GROUP BY'), r'GROUPBY')]

SEP = '$'
MAIN_ENT = '{ENT1}'


def tokenize_nl(nl_string):
    """
    tokenize NL query string into list

    punctuation and suffixes beginning with ' are treated as individual tokens
    other tokens are split at spaces

    :param str nl_string:
    :return list: list of tokens (strings)
    """

    # surround every occurrence of , ! ? ( or ) with spaces
    nl_string = re.sub(RE_SPECIAL_CHAR_SPACE, r' \1 ', nl_string)
    # surround a single quote followed by letter(s) with spaces
    nl_string = re.sub(RE_APOSTROPHE, r" '\1 ", nl_string)
    # precede . at the end of the string or followed by whitespace with space
    nl_string = re.sub(RE_FULL_STOP, " .", nl_string)

    return nl_string.split()


def tokenize_sql(query_string):
    """
    tokenize SQL template string into list

    separates != <= >= \\,!?;+*<>()=/- through whitespace
    splits at whitespace into tokens

    :param str query_string: SQL query template string
    :return list: list of tokens
    """

    # surround any of the following special characters with spaces: \,!?;+*<>()=/-
    query_string = re.sub(RE_SPECIAL_CHAR, r' \1 ', query_string)
    # remove whitespace in !=, <=, >=
    query_string = re.sub(RE_SQL_SPACE, r'\1\2', query_string)

    return query_string.split()


def groupable(query):
    """
    determine if a sql query string can have GROUP BY template created from it

    first negates for queries containing a blacklisted token
    then confirms queries with a whitelisted token
    negates the rest

    :param str query:
    :return bool: whether a GROUP BY template can be created from this query
    """

    blacklist = {'GROUP BY', 'ARG', 'COUNT_COND', 'NOT'}
    whitelist = {'MAX', 'MIN', 'SUM', 'COUNT', 'AVG', 'min', 'max', 'sum', 'count', 'avg', 'FUNC', 'funcCommand'}
    if any(token in query for token in blacklist):
        return False
    if any(token in query for token in whitelist):
        return True
    return False


def list_replace(str_list, original, substring, standalone):
    """
    in a list of strings replaces all occurrences of the original string

    if a list element is equal to the  original string apart from whitespace, replace element with the standalone string
    if an element contains the original string amongst other substrings, replace occurrences with new substring

    :param str_list: the list of string that will be altered
    :param original: the string to be replaced
    :param substring: the replacement if replacing a substring
    :param standalone: the replacement if replacing an entire list element
    """

    for i in range(0, len(str_list)):
        if original == str_list[i].strip():
            str_list[i] = standalone
        elif original in str_list[i]:
            str_list[i] = str_list[i].replace(original, substring)


def get_argmin_max_arguments(sql_string):
    """
    retrieves the arguments for the first argmin/argmax in the sql string as string

    :param str sql_string: sql query
    :return str: arguments for the first argmin/argmax
    """

    match = RE_ARG.search(sql_string)
    if not match:
        return None, None

    arg_ops = 'MIN' if 'min' in match.group() else 'MAX'
    parenthesis_open = 1
    args = ""
    for character in sql_string[match.end():]:
        if character == '(':
            parenthesis_open += 1
        if character == ')':
            parenthesis_open -= 1
            if parenthesis_open < 1:
                break
        args += character

    return args, arg_ops


def translate_argmax_min(sql_string):
    """
    iteratively and recursively substitute all argmax/argmin templates

    :param str sql_string: sql query
    :return str: new sql query
    """

    sql_string = sql_string.replace('argmax(', 'argmax (')
    sql_string = sql_string.replace('argmin(', 'argmin (')

    while 'argmax' in sql_string or 'argmin' in sql_string:
        (arg_parameters, arg_type) = get_argmin_max_arguments(sql_string)
        match_split = arg_parameters.split(SEP)
        assert len(match_split) > 2, f'not enough arguments for arg in query {sql_string}'
        arg_column = match_split[0].strip()
        arg_table = match_split[1].strip()
        if len(match_split) == 3:
            arg_where = match_split[2].strip()
        else:
            arg_where = SEP.join(match_split[2:])
            arg_where = translate_argmax_min(arg_where)

        arg_clause = f'{arg_column} = (SELECT {arg_type}({arg_column}) FROM {arg_table}'
        arg_clause += (')' if arg_where == '' else f' WHERE {arg_where}) AND {arg_where} ')

        to_replace = 'arg' + arg_type.lower() + ' (' + arg_parameters + ')'
        sql_string = sql_string.replace(to_replace, arg_clause)

    return sql_string


def simplify_sql(sql_string):
    """
    simplify generated sql queries through substitutions

    :param str sql_string: sql query as string
    :return str: simplified sql query as string
    """

    simple_sql_string = sql_string

    for pair in SIMPLIFY_SQL:
        simple_sql_string = re.sub(pair[0], pair[1], simple_sql_string)
    return simple_sql_string


def bfs_paths(graph, start, goal):
    """
    breadth first search to find connecting paths in a graph and return shortest first through a generator

    :param dict graph: dictionary with nodes of the graph as keys and a list of directly connected nodes as values
    :param str start: starting node
    :param str goal: destination node
    :return generator: list of connecting paths, shortest first
    """

    queue = [(start, [start])]

    while queue:
        (node, path) = queue.pop(0)
        for next_node in set(graph[node]) - set(path):
            if next_node == goal:
                yield path + [next_node]
            else:
                queue.append((next_node, path + [next_node]))


def create_join_string(table1, table2, schema, join_type):
    """
    create join statement for two given tables

    :param str table1: first table name
    :param str table2: second table name
    :param Schema schema: schema of the DB
    :param str join_type: type of join, either JOIN_FROM or JOIN_WHERE
    :return str: join statement
    """

    assert join_type in {'JOIN_FROM', 'JOIN_WHERE'}, f'join function {join_type} is unknown'

    if table1 == table2:
        logging.warning('attempted aggregation over one table')
        if join_type == 'JOIN_FROM':
            return table1
        else:
            return ''

    # joins = []
    # paths = bfs_paths(schema.links, table1, table2)
    #
    # best_p = next(paths, None)
    # if not best_p:
    #     return None
    #
    # if join_type == 'JOIN_FROM':
    #     return ' JOIN '.join(best_p)
    #
    # for i in range(0, len(best_p) - 1):
    #     joins.append(best_p[i] + '.' + schema.links[best_p[i]][best_p[i + 1]] + ' = ' + best_p[i + 1] + '.' +
    #                  schema.links[best_p[i + 1]][best_p[i]])
    #
    # return ' AND '.join(joins)
    if table2 in schema.links[table1]:
        if join_type == 'JOIN_FROM':
            return f'{table1} JOIN {table2}'
        else:
            return f'{table1}.{schema.links[table1][table2]} = {table2}.{schema.links[table2][table1]}'
    else:
        logging.info('No link found for JOIN with directly linked tables. Recursive JOIN not yet implemented')
        return None


def join_col(table1, table2, schema):
    """
    create join

    :param str table1: first table name
    :param str table2: second table name
    :param schema: schema of the DB
    :return:
    """

    if table1 == table2:
        logging.warning('attempted aggregation over one table')
        return None

    # paths = bfs_paths(schema.links, table1, table2)
    #
    # best_p = next(paths, None)
    # if not best_p:
    #     return None
    #
    # if len(best_p) > 2:
    #     logging.warning('No link found for JOIN with directly linked tables. Recursive JOIN not yet implemented')
    #     return None
    #
    # return f'{best_p[0]}.{schema.links[best_p[0]][best_p[1]]}'

    if table2 in schema.links[table1]:
        return f'{table1}.{schema.links[table1][table2]}'
    else:
        logging.info('No link found for JOIN with directly linked tables. Recursive JOIN not yet implemented')
        return None
