#!/usr/bin/env python3
""" script verifying your templates file by asserting certain conditions for each line
"""

from generation.generator_utils import read_lines_from_file


def check_template_conditions(template_line):
    """
    assert conditions on a lien from a template file

    raises assertion error if condition is not fulfilled

    :param str template_line: line (excluding empty and comments) from a templates file
    """

    queries = template_line.split('\t')
    assert (len(queries) > 1), f'Malformed input in templates, no tab in {template_line}'
    for template in queries:
        assert template.count('(') == template.count(')'), f'unbalanced parenthesis count in {template}'
    nl_queries = template_line[:-1]
    sql_query = template_line[-1]
    assert 'SELECT' in sql_query.split(), f'Last query in {template_line} is not a valid sQL query'
    assert all(('SELECT' not in query for query in nl_queries)), f'More than one SQL query in {template_line}'


if __name__ == '__main__':
    """ through asserts check that for each line in the templates file conditions are fulfilled
    """
    templates = read_lines_from_file('data/templates.txt')

    for line in templates:
        check_template_conditions(line)
