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


def draw_rack(
    height, width=64,
    labels=(), positions=(), heights=(),
    display=True
):
    """
    Create an ASCII-art representation of a server rack given a list of
    device labels, positions, and heights, and optionally print it
    to standard output.

    :param int height: The height of the rack (U)
    :param int width: Display width to reserve for labels
    :param list(str) labels: Names of the devices in the rack
    :param list(int) positions: Positions of the devices in the rack
    :param list(int) heights: Heights of the devices in the rack
    :param bool display: print the result if True

    :returns: ASCII-art representation of the rack as a list of strings,
        one per line.
    :rtype: list(str)
    """
    devices = list(zip(positions, heights, labels))
    devices.sort(reverse=True)
    devices.insert(0, None)

    spacer = '+----+' + '-'*width + '+'
    emptyslot = '|    |' + ' '*width + '|'
    
    drawing = []
    u = 1
    device_top = True
    current_device = devices.pop()

    while (u <= height):
        if current_device and current_device[0] == u:
            drawing.append(spacer)
            label = current_device[2][:width-3].ljust(width-3)
            drawing.append('|U{:03}|| {}||'.format(u, label))
            u += 1
            for _ in range(current_device[1] - 1):
                drawing.append('|    ||' + ' '*(width-2) + '||')
                drawing.append('|U{:03}||{}||'.format(u, ' '*(width-2)))
                u += 1
            current_device = devices.pop()
            device_top = True
        else:
            if device_top:
                drawing.append(spacer)
            else:
                drawing.append(emptyslot)
            drawing.append('|U{:03}|{}|'.format(u, ' '*width))
            device_top = False
            u += 1

    drawing.append(spacer)
    drawing.reverse()

    if display:
        for line in drawing:
            print(line)

    return drawing
