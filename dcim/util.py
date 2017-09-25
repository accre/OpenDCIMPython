"""
General stand-alone utility functions for internal package use
"""
import re
import string


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
