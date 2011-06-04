# Standard library imports
import unittest

# Geo library imports
from enthought.contexts.name_filter_context import NameFilterContext


class NameFilterContextTestCase(unittest.TestCase):
    """ Test whether the context filters values by their name appropriately.

        Note: We can't run all the AbstractContextTestCases on this class
              because it is picky about what variables it allows to be
              assigned into it, and many of the tests will fail.
    """

    ##########################################################################
    # TestCase interface
    ##########################################################################

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    ##########################################################################
    # NameFilterContextTestCase interface
    ##########################################################################

    def test_allows(self):
        """ Does the allow method filter names appropriately?
        """
        context = NameFilterContext(names=['foo'])

        self.assertTrue(context.allows(1,'foo'))
        self.assertFalse(context.allows(1,'bar'))

    def test_set_allowed_name(self):
        """ Does the context accept names that aren't in its name list?
        """
        context = NameFilterContext(names=['foo'])

        context['foo'] = 1
        self.assertEqual(context['foo'], 1)
        self.assertFalse(context.allows(1,'bar'))

    def test_set_disallowed_name(self):
        """ Does the context reject names that aren't in its name list?
        """
        context = NameFilterContext(names=['foo'])

        def bad_name():
            context['bar'] = 2

        self.assertRaises(ValueError, bad_name)

    def test_default_list(self):
        """ Do all NameFilterContext get their own list by default?

            Note: This is really a test that the default value to an Any trait
                  is not shared between objects if it is a list...
        """
        context1 = NameFilterContext()
        context2 = NameFilterContext()
        context1.names.append('foo')
        context2.names.append('bar')

        self.assertEqual(context1.names, ['foo'])
        self.assertEqual(context2.names, ['bar'])


def test_checkpoint():
    d = NameFilterContext(names=['a', 'b'])
    d['a'] = object()
    d['b'] = object()
    copy = d.checkpoint()
    assert copy is not d
    assert copy.subcontext is not d.subcontext
    assert set(copy.keys()) == set(d.keys())
    assert copy['a'] is d['a']
    assert copy['b'] is d['b']

    assert copy.names == d.names
    assert copy.names is not d.names


def test_checkpoint_nested():
    d = NameFilterContext(names=['a', 'b'], subcontext=NameFilterContext(names=['a', 'b']))
    d['a'] = object()
    d['b'] = object()
    copy = d.checkpoint()
    assert copy is not d
    assert copy.subcontext is not d.subcontext
    assert copy.subcontext.subcontext is not d.subcontext.subcontext
    assert set(copy.keys()) == set(d.keys())
    assert copy['a'] is d['a']
    assert copy['b'] is d['b']

    assert copy.names == d.names
    assert copy.names is not d.names
    assert copy.subcontext.names == d.subcontext.names
    assert copy.subcontext.names is not d.subcontext.names


if __name__ == '__main__':
    unittest.main()
