"""
Tests for the utils module
"""
from textwrap import dedent

from dcim.util import (
    expand_brackets,
    draw_rack
)


class TestBracketExpand:
    """
    Tests for the expand_brackets function
    """
    def test_no_brackets(self):
        assert expand_brackets('foobaz') == ['foobaz']

    def test_invalid_brackets(self):
        assert expand_brackets('foo[bar123]') == ['foo[bar123]']

    def test_valid_range(self):
        assert expand_brackets('qu[1-3]ux') == ['qu1ux', 'qu2ux', 'qu3ux']

    def test_single_range(self):
        assert expand_brackets('foo[107-107]') == ['foo107']

    def test_null_range(self):
        assert expand_brackets('foo[9-7]') == []


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
