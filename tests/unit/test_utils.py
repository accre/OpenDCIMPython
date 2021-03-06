"""
Tests for the utils module
"""
from io import StringIO
from textwrap import dedent

import pytest

from dcim.util import (
    expand_hostlist,
    expand_numlist,
    draw_rack,
    normalize_label,
    DHCPDHostParser,
)

class TestHostlistExpand:
    """
    Tests for the expand_hostlist and numlist functions

    Taken from https://github.com/appeltel/slurmlint
    """
    def test_expand_numlist(self):
        expected = [
            '05', '06', '07', '009', '010', '011', '012', '013', '04', '4'
        ]
        assert expand_numlist('05-07,009-13,04,4') == expected

        expected = ['5', '123', '5017', '5018', '5019']
        assert expand_numlist('5,123,5017-5019') == expected


    def test_expand_hostlist(self):
        expected = [
            'ng032', 'cn304', 'cn305', 'cn306', 'cn308', 'gpu0012', 'gpu0013',
            'gpu0014', 'gpu0015', 'gpu0022', 'gpu0023', 'gpu0024', 'gpu0025'
        ]
        result = expand_hostlist('ng032,cn[304-306,308],gpu00[1-2][2-5]')
        assert result == expected



class TestDrawRack:
    """
    Tests for the draw_rack function
    """
    def test_empty_rack(self):
        expected = """
            +----+----------------------------------------+
            |U008|                                        |
            |    |                                        |
            |U007|                                        |
            |    |                                        |
            |U006|                                        |
            |    |                                        |
            |U005|                                        |
            |    |                                        |
            |U004|                                        |
            |    |                                        |
            |U003|                                        |
            |    |                                        |
            |U002|                                        |
            |    |                                        |
            |U001|                                        |
            +----+----------------------------------------+
        """
        expected = dedent(expected).strip()

        result = draw_rack(8, width=40, display=False)

        assert expected == '\n'.join(result)

    def test_non_adjacent_devices(self):
        expected = """
            +----+----------------------------------------+
            |U008|                                        |
            +----+----------------------------------------+
            |U007||                                      ||
            |    ||                                      ||
            |U006||                                      ||
            |    ||                                      ||
            |U005|| bar                                  ||
            +----+----------------------------------------+
            |U004|                                        |
            |    |                                        |
            |U003|                                        |
            +----+----------------------------------------+
            |U002|| foo                                  ||
            +----+----------------------------------------+
            |U001|                                        |
            +----+----------------------------------------+
        """
        expected = dedent(expected).strip()

        result = draw_rack(8, width=40, display=False,
            labels=['foo', 'bar'],
            positions=[2, 5],
            heights=[1, 3]
        )

        assert expected == '\n'.join(result)

    def test_adjacent_devices(self):
        expected = """
            +----+----------------------------------------+
            |U008||                                      ||
            |    ||                                      ||
            |U007||                                      ||
            |    ||                                      ||
            |U006||                                      ||
            |    ||                                      ||
            |U005|| baz                                  ||
            +----+----------------------------------------+
            |U004||                                      ||
            |    ||                                      ||
            |U003||                                      ||
            |    ||                                      ||
            |U002|| bar                                  ||
            +----+----------------------------------------+
            |U001|| foo                                  ||
            +----+----------------------------------------+
        """
        expected = dedent(expected).strip()

        result = draw_rack(8, width=40, display=False,
            labels=['foo', 'bar', 'baz'],
            positions=[1, 2, 5],
            heights=[1, 3, 4]
        )

        assert expected == '\n'.join(result)


class TestNormalizeLabel:
    """
    Tests for the normalize label function
    """
    def test_already_normalized(self):
        assert normalize_label('x11-a22-b-9') == 'x11-a22-b-9'
    def test_normalize_case1(self):
        assert normalize_label('SM_29 H11') == 'sm-29-h11'
    def test_normalize_case2(self):
        assert normalize_label('ToR--G3 Dell X290.a') == 'tor-g3-dell-x290-a'
    def test_not_normalizable(self):
        with pytest.raises(ValueError) as cm:
            normalize_label('G3**_+;')
        assert 'G3**_+;' in str(cm.value)


class TestDHCPDHostParser:
    """
    Tests for the util.DCHPDHostParser class
    """
    def test_tokenize_valid_block(self):
        dhcpd_raw = """\
            # 10.0.5.1/24 - x250b-4g-u44 - vlan12
            pool {
              deny members of "IPMI";
              allow members of "vlan12";
              option routers 10.0.12.1;
              option subnet-mask 255.255.255.0;
              option classless-static-routes 20.10.0 10.0.12.1, 0 10.0.12.1;
              default-lease-time 1800; # 30 min 
              max-lease-time 3600; # 1 hr
              range 10.0.12.131 10.0.12.220;
            }
        """
        dhcpd_stream = StringIO(dedent(dhcpd_raw))

        expected = [
            'pool', '{',
            'deny', 'members', 'of', 'IPMI', ';',
            'allow', 'members', 'of', 'vlan12', ';',
            'option', 'routers', '10.0.12.1', ';',
            'option', 'subnet-mask', '255.255.255.0', ';',
            'option', 'classless-static-routes', '20.10.0',
                '10.0.12.1', ',', '0', '10.0.12.1', ';',
            'default-lease-time', '1800', ';',
            'max-lease-time', '3600', ';',
            'range', '10.0.12.131', '10.0.12.220', ';',
            '}'
        ]

        parser = DHCPDHostParser()

        assert parser.tokenize(dhcpd_stream) == expected

    def test_tokenize_valid_block2(self):
        dhcpd_raw = """\
            ########################################################
            ## Brood 7 (node081-node120)
            ########################################################

            use-host-decl-names on;

            group {

                option routers 10.0.18.1;
                option subnet-mask 255.255.252.0;
                option classless-static-routes 42.10.0 10.0.18.1;

                    host node098 {
                           hardware ethernet 54:1A:77:2f:70:10;
                    fixed-address 10.0.18.2;
                    }
                    host node099 {
                           hardware ethernet 54:1A:77:2f:70:4d;
                    fixed-address 10.0.18.3;
                    }
            }
        """
        dhcpd_stream = StringIO(dedent(dhcpd_raw))

        expected = [
            'use-host-decl-names', 'on', ';',
            'group', '{',
            'option', 'routers', '10.0.18.1', ';',
            'option', 'subnet-mask', '255.255.252.0', ';',
            'option', 'classless-static-routes', '42.10.0', '10.0.18.1', ';',
            'host', 'node098', '{',
            'hardware', 'ethernet', '54:1a:77:2f:70:10', ';',
            'fixed-address', '10.0.18.2', ';',
            '}',
            'host', 'node099', '{',
            'hardware', 'ethernet', '54:1a:77:2f:70:4d', ';',
            'fixed-address', '10.0.18.3', ';',
            '}',
            '}'
        ]

        parser = DHCPDHostParser()

        assert parser.tokenize(dhcpd_stream) == expected

    def test_parse_two_hosts(self):

        tokenlist = [
            'use-host-decl-names', 'on', ';',
            'group', '{',
            'option', 'routers', '10.0.18.1', ';',
            'option', 'subnet-mask', '255.255.252.0', ';',
            'option', 'classless-static-routes', '42.10.0', '10.0.18.1', ';',
            'host', 'node098', '{',
            'hardware', 'ethernet', '54:1a:77:2f:70:10', ';',
            'fixed-address', '10.0.18.2', ';',
            '}',
            'host', 'node099', '{',
            'hardware', 'ethernet', '54:1a:77:2f:70:4d', ';',
            'fixed-address', '10.0.18.3', ';',
            '}',
            '}'
        ]

        parser = DHCPDHostParser()
        parser.parse_tokens(tokenlist)

        assert len(parser) == 2

        assert parser['node098']['hardware ethernet'] == '54:1a:77:2f:70:10'
        assert parser['node098']['fixed-address'] == '10.0.18.2'

        assert parser['node099']['hardware ethernet'] == '54:1a:77:2f:70:4d'
        assert parser['node099']['fixed-address'] == '10.0.18.3'

    def test_tokenize_and_parse_valid_block2(self):
        dhcpd_raw = """\
            ########################################################
            ## Brood 7 (node081-node120)
            ########################################################

            use-host-decl-names on;

            group {

                option routers 10.0.18.1;
                option subnet-mask 255.255.252.0;
                option classless-static-routes 42.10.0 10.0.18.1;

                    host node098 {
                           hardware ethernet 54:1A:77:2f:70:10;
                    fixed-address 10.0.18.2;
                    }
                    host node099 {
                           hardware ethernet 54:1A:77:2f:70:4d;
                    fixed-address 10.0.18.3;
                    }
            }
        """
        dhcpd_stream = StringIO(dedent(dhcpd_raw))

        parser = DHCPDHostParser()
        parser.parse(dhcpd_stream)

        assert len(parser) == 2

        assert parser['node098']['hardware ethernet'] == '54:1a:77:2f:70:10'
        assert parser['node098']['fixed-address'] == '10.0.18.2'

        assert parser['node099']['hardware ethernet'] == '54:1a:77:2f:70:4d'
        assert parser['node099']['fixed-address'] == '10.0.18.3'

    def tokenize_and_parse_with_option(self):
        dhcpd_raw = """\
            host node099 {
                hardware ethernet 54:1A:77:2f:70:4d;
                fixed-address 10.0.18.3;
                option domain-name-servers 192.168.128.10;
                option host-name "node099.example.com";
            }
        """
        dhcpd_stream = StringIO(dedent(dhcpd_raw))

        parser = DHCPDHostParser()
        parser.parse(dhcpd_stream)

        assert len(parser) == 1

        assert parser['node099']['hardware ethernet'] == '54:1A:77:2f:70:4d'
        assert parser['node099']['fixed-address'] == '10.0.18.3'
        assert parser['node099']['option domain-name-servers'] == '192.168.128.10'
        assert parser['node099']['option host-name'] == 'node099.example.com'
