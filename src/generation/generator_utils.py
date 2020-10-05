# coding=utf-8
""" Utility methods for synthetic training data generation
"""


def read_lines_from_file(filename):
    """
    read list of lines from a file while ignoring empty lines, whitespace and comments (starting with '#')

    :param str filename: path/filename of the file to be read
    :return list: list of lines without empty lines or comments
    """
    with open(filename) as in_file:
        return [line.strip() for line in in_file if line and not line.isspace() and not line.startswith('#')]


def parse_dict(dictionary_file):
    """
    parse one mapping per line through '=>' from dictionary file

    :param str dictionary_file: path to dictionary file
    :return dict: dictionary mapping keys to values according to dict_file
    """
    lines = read_lines_from_file(dictionary_file)
    dictionary = {}

    # add to NL slot fill dict
    for line in lines:
        assert ("=>" in line), "Malformed input in dictionary file, no '=>' in: {}".format(line)
        (key, values) = line.split('=>')
        dictionary[key.strip()] = [v.strip() for v in values.split('|') if v and not v.isspace()]

    return dictionary
