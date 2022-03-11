
# Standard Library Imports
from io import BytesIO
import os

# Third-party Library Imports
from importlib_resources import files

# Local library imports
from codetools.contexts.data_context import DataContext
from codetools.contexts.tests.abstract_context_test_case import AbstractContextTestCase
from codetools.contexts.tests.test_case_with_adaptation import (
    TestCaseWithAdaptation,
)


def _create_data_context_pickle():
    """ Used to create a pickled DataContext stored in
    codetools/contexts/tests/data/data_context.pickle.

    Function is kept for reference. Do not rerun unless you need to override
    the existing pickled DataContext to be tested.
    """
    d = DataContext(name='test_context')
    d['a'] = 1
    d['b'] = 2

    filename = os.fspath(
        files('codetools.contexts.tests') / 'data' / 'data_context.pickle'
    )
    d.save(filename)

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


class RestrictedValues(DataContext):
    """ Only allow some values.
    """

    def allows(self, value, name=None):
        return isinstance(value, int)


class RestrictedKeys(DataContext):
    """ Only allow some keys.
    """

    def allows(self, value, name=None):
        return name == 'a'


class TestPersistence(TestCaseWithAdaptation):
    def test_persistence(self):
        """ Can DataContexts round-trip through the persistence mechanism?
        """
        d = DataContext(name='test_context')
        d['a'] = 1
        d['b'] = 2

        f = BytesIO()
        d.save(f)
        f.seek(0, 0)
        d2 = DataContext.load(f)

        assert d.name == d2.name
        assert set(d2.keys()) == set(['a', 'b'])
        assert d2['a'] == d['a']
        assert d2['b'] == d['b']

    def test_persistence_backwards_compatibility(self):
        filename = os.fspath(
            files('codetools.contexts.tests') / 'data' / 'data_context.pickle'
        )
        d = DataContext.load(filename)

        assert d.name == 'test_context'
        assert set(d.keys()) == set(['a', 'b'])
        assert d['a'] == 1
        assert d['b'] == 2

    def test_allows_values(self):
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

    def test_allows_keys(self):
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

    def test_checkpoint(self):
        d = DataContext()
        d['a'] = object()
        d['b'] = object()
        copy = d.checkpoint()
        assert copy is not d
        assert copy.subcontext is not d.subcontext
        assert set(copy.keys()) == set(d.keys())
        assert copy['a'] is d['a']
        assert copy['b'] is d['b']

    def test_checkpoint_nested(self):
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

    def test_comparison(self):
        class _TestContext(DataContext):
            pass
        a = DataContext(name='a')
        b = DataContext(name='b')
        c = _TestContext(name='c')

        assert a == b
        assert a != c
