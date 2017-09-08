"""
General stand-alone utility functions for internal package use
"""
import re


BRACKETRANGE_RE = re.compile(r"\[([0-9]+-[0-9]+)\]")


def expand_brackets(input_string):
    """
    Take a string of the form "node[1-12]" and return a list of strings
    of the form ["node1", "node2", ..., "node12"]. If there is not a valid
    bracket range, return a list containing only the input string.
    """
    match = BRACKETRANGE_RE.search(input_string)
    if match is None:
        return [input_string]

    start, end = [int(n) for n in match.group(1).split('-')]
    prefix = input_string.split('[')[0]
    suffix = input_string.split(']')[-1]

    return ['{}{}{}'.format(prefix, x, suffix) for x in range(start, end+1)]
