"""
General stand-alone utility functions for internal package use
"""
import re
import string


RE_ISNUM = re.compile('[0-9]+')
RE_NEXTBRACKET = re.compile('([^[]*)\[([^]]*)\](.*)')

VALID_LABEL_RE = re.compile(r"^[a-z0-9-]*$")


def expand_hostlist(hostlist, max_depth=20):
    """
    Given a slurm-style list of hosts, expand and
    return individual hostnames.

    Copied from https://github.com/appeltel/slurmlint

    :param str hostlist: slurm-style host list
    :param int max_depth: maximum number of brackets in an entry
    :returns: list of hostnames
    :rtype: list(str)
    """
    result = _split_outside_brackets(hostlist, ',')
    depth = 0
    while depth < max_depth:
        if not any(host.endswith(']') for host in result):
            return result
        depth += 1

        new_result = []
        for item in result:
            if not item.endswith(']'):
                new_result.append(item)
            else:
                new_result.extend(_expand_next_bracket(item))

        result = new_result

    raise ValueError('Too many brackets') 


def _split_outside_brackets(raw, splitchar):
    """
    Split a string on a given character only when the
    character is outside brackets
    Nested brackets are right out

    Copied from https://github.com/appeltel/slurmlint
    """
    result = []
    word = ''
    in_brackets = False
    for char in raw:
        if char == '[' and not in_brackets:
            word = word + char
            in_brackets = True
        elif char == '[' and in_brackets:
            raise ValueError('Nested brackets are right out')
        elif char == ']' and in_brackets:
            word = word + char
            in_brackets = False
        elif char == ']' and not in_brackets:
            raise ValueError('Unmatched end-bracket')
        elif not in_brackets and char == splitchar and word:
            result.append(word)
            word = ''
        elif not in_brackets and char == splitchar and not word:
            raise ValueError('Missing item between separator')
        else:
            word = word + char
    if not word:
        raise ValueError('Missing item after separator')
        
    result.append(word)
    return result


def _expand_next_bracket(hostlist):
    """
    Take a hostlist and expand the next set of brackets
    returning a list of either hosts or hostlists if
    there are multiple brackets.

    Copied from https://github.com/appeltel/slurmlint
    """
    if not hostlist.endswith(']'):
        raise ValueError(
            'Invalid host list, not ending in bracket'
        )
    match = RE_NEXTBRACKET.match(hostlist)
    if not match:
        raise ValueError('Invalid brackets in host list')
    prefix = match.group(1)
    numlist = match.group(2)
    suffix = match.group(3)
    return [prefix + num + suffix for num in expand_numlist(numlist)] 


def expand_numlist(raw):
    """
    Expand a comma-delimited list of numbers and/or numeric ranges

    Copied from https://github.com/appeltel/slurmlint

    :param str raw: String containing list of numbers to be expanded
    :returns: List of expanded numbers
    :rtype: list(str)
    """
    result = []
    for item in raw.split(','):
        if not '-' in item:
            if not RE_ISNUM.match(item):
                raise ValueError('Invalid numeric value')
            result.append(item)
            continue

        vals = item.split('-')
        if not len(vals) == 2:
            raise ValueError('Invalid numeric range')
        result.extend(_expand_numrange(vals[0], vals[1]))
    return result


def _expand_numrange(first, last):
    """
    Expand a range of numbers that may be zero-prefixed into a list

    Copied from https://github.com/appeltel/slurmlint
    """
    if not RE_ISNUM.match(first) or not RE_ISNUM.match(last):
        raise ValueError('Invalid numeric value')
    if int(last) < int(first):
        raise ValueError('Invalid range')

    fixed = first.startswith('0')
    if fixed:
        return [
            str(val).zfill(len(first))
            for val in range(int(first), int(last) + 1)
        ]

    return [str(val) for val in range(int(first), int(last) + 1)]


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


def normalize_label(raw_label):
    """
    Normalize a label (str) to a policy of only containing lowercase
    letters (a-z), numbers, and ``-``. Remove leading or trailing
    whitespace, lowercase letters, and replace internal whitespace,
    underscores, dots, or colons  with a single ``-`` character
    between letters. Return the resulting normalized label.

    If the label cannot be normalized in this manner, raise a ValueError.

    :param str raw_label: Device label to be normalized
    :returns: Normalized label
    """
    label = raw_label.strip().lower()
    label = re.sub(r"[\s\-_\.:]+", '-', label)

    if not VALID_LABEL_RE.search(label):
        raise ValueError(
            'Label "{}" could not be normalized to contain only a-z, 0-9, '
            'and "-" using the available rules.'.format(raw_label)
        )

    return label


class DHCPDHostParser(dict):
    """
    Used to parse host blocks out of dchpd configuration files
    for easy access to IPs and MACs in a dictionary format.

    For example, if a dchpd.conf file had a host block like the following::

        host node099 {
            hardware ethernet 54:1A:77:2f:70:4d;
            fixed-address 10.0.18.3;
            option domain-name-servers 192.168.128.10;
            option host-name "node099.example.com";
        }

    Then parsing the file with the parser object would result in the
    following dict set to the key ``parser['node099']`` after parsing
    the file::

        {
            'hardware ethernet': '54:1A:77:2f:70:4d',
            'fixed-address': '10.0.18.3',
            'option domain-name-servers': '192.168.128.10',
            'option host-name': 'node099.example.com'
        }

    Note that repeated declarations or parameters in a single host block
    will result in clobbering the first declaration, as will multiple
    host blocks in the same stream. This simple parser is based on
    my very limited understanding of dhcpd conf syntax!
    """
    def __init__(self, stream=None):
        """
        Initialize the parser state. If a stream is given it is parsed
        and hosts added to the object dict.

        :param stream stream: File-like object to read and parse
        """
        if stream is not None:
            self.parse(stream)

    def parse(self, stream):
        """
        Parse a file-like dchpd.conf object and load the declarations
        from all host blocks into the object dictionary keyed by
        host.

        :param stream stream: file-like dchpd.conf object open for reading
        """
        self.tokenize(stream)
        self.parse_tokens()

    def parse_tokens(self, tokenlist=None):
        """
        Parse a list of dchpd.conf token strings and load the declarations
        from all host blocks into the object dictionary keyed by
        host. If no list is given use the previous results of the
        ``tokenize`` method.

        :param list(str) tokenlist: list of dhcpd.conf token strings
        """
        if tokenlist is not None:
            self.t_result = tokenlist

        self.p_munch_func = self._p_munch_normal
        self.t_result.reverse()

        while self.t_result:
            self.p_munch_func()

    def _p_munch_normal(self):
        """munch tokens and change state if it's "host" """
        token = self.t_result.pop()
        if token == 'host':
            self.p_munch_func = self._p_munch_host

    def _p_munch_host(self):
        """parse a host block and add to internal dict"""
        # next token should be the hostname
        self.cur_hostname = self.t_result.pop()
        self[self.cur_hostname] = {}

        if self.t_result.pop() != '{':
            raise ValueError(
                'Expected open curly-brace after host {}'.format(hostname)
            )

        self.p_munch_func = self._p_munch_host_entry

    def _p_munch_host_entry(self):
        """parse an entry within a host block"""
        token = self.t_result.pop()

        # end of host block
        if token == '}':
            self.p_munch_func = self._p_munch_normal
            return

        # empty host entry line
        if token == ';':
            return

        # if the token is 'hardware' or 'option' then combine with the
        # next token for convienience
        if token == 'hardware' or token == 'option':
            token = '{} {}'.format(token, self.t_result.pop())

        key = token
        val = []
        token = self.t_result.pop()
        while token != ';':
            val.append(token)
            token = self.t_result.pop()

        self[self.cur_hostname][key] = ' '.join(val)

    def tokenize(self, stream):
        """
        Read a file-like object and break into a list of tokens corresponding
        to the (approximate) dhcpd.conf file grammar. Comments are removed
        completely, non-quoted words lowercased, whitespace removed, curly
        braces and semicolons separated into their own tokens. The list of
        tokens is returned and set to the object attribute ``t_result``.

        Internally, the tokenizer is set up as a finite state machine. The
        raw string is munched character by character, with the current token
        being built in the ``cur_token`` attribute. For each character
        a function is called to munch the character, and the specific function
        to be called is determined by the current state: normal, comment,
        squote, dquote, or postquote. A reference to the function for the
        current state is held in the attribute ``t_munch_func``.

        :param stream stream: File-like object to read and tokenize:

        :returns: List of dhcpd.conf token strings
        :rtype: list(str)
        """
        self.t_munch_func = self._munch_normal
        self.t_result = []
        self.cur_token = []

        raw_string = list(stream.read())

        idx = 1
        line = 1
        for char in raw_string:
            self.t_munch_func(char, idx, line)
            if char == '\n':
                line += 1
                idx = 1
            else:
                idx += 1
        return self.t_result

    def _t_push_token(self, extender=''):
        """
        Pushes the current token onto the result list along with
        the additional string extender added to the token, if the
        current token is nonempty. Resets the current token to empty.
        """
        for char in extender:
            self.cur_token.append(char)
        if self.cur_token:
            self.t_result.append(''.join(self.cur_token))
        self.cur_token = []

    def _munch_normal(self, char, idx, line):
        """munch next character in NORMAL state"""
        if char == '\'':
            if self.cur_token:
                raise ValueError(
                    'Unexpected quote at line {} position {}'
                    .format(line, idx)
                )
            self.t_munch_func = self._munch_squote

        elif char == '"':
            if self.cur_token:
                raise ValueError(
                    'Unexpected quote at line {} position {}'
                    .format(line, idx)
                )
            self.t_munch_func = self._munch_dquote

        elif char in string.whitespace:
            self._t_push_token()

        elif char in ',;':
            self._t_push_token()
            self._t_push_token(char)

        elif char == '#':
            self._t_push_token()
            self.t_munch_func = self._munch_comment

        else:
            self.cur_token.append(char.lower())

    def _munch_comment(self, char, idx, line):
        """munch next character in COMMENT state"""
        if char == '\n':
            self.t_munch_func = self._munch_normal

    def _munch_squote(self, char, idx, line):
        """munch next character in SQUOTE state"""
        if char == '\'':
            self._t_push_token()
            self.t_munch_func = self._munch_postquote
        else:
            self.cur_token.append(char)

    def _munch_dquote(self, char, idx, line):
        """munch next character in DQUOTE state"""
        if char == '"':
            self._t_push_token()
            self.t_munch_func = self._munch_postquote
        else:
            self.cur_token.append(char)

    def _munch_postquote(self, char, idx, line):
        """munch next character in POSTQUOTE state"""
        allowed = string.whitespace + ',;#'
        if char not in allowed:
            raise ValueError(
                'Unexpected character {} after close quote at line {} pos {}'
                .format(char, line, idx)
            )

        elif char in ',;':
            self._t_push_token(char)
            self.t_munch_func = self._munch_normal
        elif char == '#':
            self.t_munch_func = self._munch_comment
        else:
            self.t_munch_func = self._munch_normal
