
# Standard Library Imports
from cStringIO import StringIO
import sys

import nose

# Local library imports
from codetools.contexts.data_context import DataContext
from codetools.contexts.tests.abstract_context_test_case import AbstractContextTestCase


class DataContextTestCase(AbstractContextTestCase):

    #### AbstactContextTestCase interface ######################################

    def context_factory(self, *args, **kw):
        """ Return the type of context we are testing.
        """
        return DataContext(*args, **kw)

    def matched_input_output_pair(self):
        """ Return values for testing dictionary get/set, etc.
        """
        return 1.2, 1.2


def test_persistence():
    """ Can DataContexts round-trip through the persistence mechanism?
    """
    d = DataContext(name='test_context')
    d['a'] = 1
    d['b'] = 2

    f = StringIO()
    d.save(f)
    f.seek(0, 0)
    d2 = DataContext.load(f)

    assert d.name == d2.name
    assert set(d2.keys()) == set(['a', 'b'])
    assert d2['a'] == d['a']
    assert d2['b'] == d['b']


class RestrictedValues(DataContext):
    """ Only allow some values.
    """

    def allows(self, value, name=None):
        return isinstance(value, int)


def test_allows_values():
    r = RestrictedValues()
    # This should work.
    r['a'] = 1
    # This shouldn't.
    try:
        r['b'] = 'bad'
    except ValueError:
        pass
    else:
        assert False, "should have raised ValueError"


class RestrictedKeys(DataContext):
    """ Only allow some keys.
    """

    def allows(self, value, name=None):
        return name == 'a'


def test_allows_keys():
    r = RestrictedKeys()
    # This should work.
    r['a'] = 1
    # This shouldn't.
    try:
        r['b'] = 'bad'
    except ValueError:
        pass
    else:
        assert False, "should have raised ValueError"


def test_checkpoint():
    d = DataContext()
    d['a'] = object()
    d['b'] = object()
    copy = d.checkpoint()
    assert copy is not d
    assert copy.subcontext is not d.subcontext
    assert set(copy.keys()) == set(d.keys())
    assert copy['a'] is d['a']
    assert copy['b'] is d['b']


def test_checkpoint_nested():
    d = DataContext(subcontext=DataContext())
    d['a'] = object()
    d['b'] = object()
    copy = d.checkpoint()
    assert copy is not d
    assert copy.subcontext is not d.subcontext
    assert copy.subcontext.subcontext is not d.subcontext.subcontext
    assert set(copy.keys()) == set(d.keys())
    assert copy['a'] is d['a']
    assert copy['b'] is d['b']

def test_comparison():
    class _TestContext(DataContext):
        pass
    a = DataContext(name='a')
    b = DataContext(name='b')
    c = _TestContext(name='c')

    assert a == b
    assert a != c

