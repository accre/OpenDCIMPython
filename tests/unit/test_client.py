"""
Tests for the dcim.DCIMClient class that can be performed without
interacting with an OpenDCIM server. This can be accomplished by
pre-populating the cache with some device, cabinet, and datacenter
requests.
"""
import pytest
from textwrap import dedent

from dcim.client import DCIMClient

from tests.assets.client_responses import populate_cache


@pytest.fixture
def client():
    c = DCIMClient(caching=True)
    c.cache = populate_cache()
    return c


class TestClientLocate:
    """
    Tests for the DCIMClient.locate method
    """
    def test_no_parents(self, client):
        expected = {
            'datacenter': 'Foo 101',
            'cabinet': 'A01',
            'position': 1,
            'parent_devices': []
        }
        assert client.locate('node101') == expected

    def test_parents(self, client):
        expected = {
            'datacenter': 'Foo 101',
            'cabinet': 'A01',
            'position': 4,
            'parent_devices': ['chassisA']
        }
        assert client.locate('node103') == expected


class TestClientModel:
    """
    Tests for the DCIMClient.model method
    """
    def test_no_template(self, client):
        expected = {
            'make': None,
            'model': None,
            'serial': 'ABCDEFGH'
        }
        assert client.model('node102') == expected

    def test_template(self, client):
        expected = {
            'make': 'Ringo',
            'model': 'PowerDrum R730',
            'serial': 'ABCDEFGH'
        }
        assert client.model('node101') == expected


class TestClientShowrack:
    """
    Tests for the client showrack function
    """
    def test_showrack(self, client):
        expected = """\
            +----+--------------------------------+
            |U010|                                |
            |    |                                |
            |U009|                                |
            |    |                                |
            |U008|                                |
            |    |                                |
            |U007|                                |
            |    |                                |
            |U006|                                |
            +----+--------------------------------+
            |U005||                              ||
            |    ||                              ||
            |U004|| chassisA (node104, node103)  ||
            +----+--------------------------------+
            |U003|                                |
            +----+--------------------------------+
            |U002|| node102                      ||
            +----+--------------------------------+
            |U001|| node101                      ||
            +----+--------------------------------+
        """
        expected = dedent(expected).strip()

        result = '\n'.join(client.showrack('A01', width=40))

        assert result == expected
