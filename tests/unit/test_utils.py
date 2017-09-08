"""
Tests for the utils module
"""
from dcim.util import expand_brackets


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
