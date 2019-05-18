# Standard library imports
from io import BytesIO
import os
import sys
import unittest

import nose
from nose.plugins.skip import SkipTest

# Enthought library imports
from traits.api import Any

# Geo library imports
from codetools.contexts.tests.abstract_context_test_case import AbstractContextTestCase
from codetools.contexts.data_context import DataContext
from codetools.contexts.multi_context import MultiContext


class MultiContextTestCase(AbstractContextTestCase):

    ############################################################################
    # AbstractContextTestCase interface
    ############################################################################

    def context_factory(self, *args, **kw):
        """ Return the type of context we are testing.
        """
        return MultiContext(DataContext(*args, **kw))

    def matched_input_output_pair(self):
        """ Return values for testing dictionary get/set, etc.
        """
        return 1.2, 1.2

    ############################################################################
    # MultiContext2TestCase interface
    ############################################################################

    def test_set_rebind_between_contexts(self):
        """ Can we rebind variables between contained contexts?
        """

        class C(DataContext):
            f = Any
            def __init__(self, f):
                super(C, self).__init__(f=f)
            def allows(self, value, name):
                return self.f(value, name)

        # `allows' predicates
        all = lambda v,n: True
        none = lambda v,n: False
        positive = lambda v,n: v > 0
        negative = lambda v,n: v < 0

        # Make a multi-context where the top context only accepts positive
        # numbers and the next one accepts anything. For robustness, add some
        # noise below.
        multi = MultiContext(C(positive), C(all),
                             C(all), C(none), C(negative)) # Noise
        [upper, lower] = multi.subcontexts[0:2]

        for a,b in [(3,8), (3,-8), (-3,8), (-3,-8)]:

            # Bind and rebind 'x'
            multi['x'] = a
            multi['x'] = b

            # 'x' should have the latter binding
            assert multi['x'] == b

            # 'x' should live in the upper context if it's positive, else in
            # the lower one
            if multi['x'] > 0:
                self.assertTrue('x' in upper)
            else:
                self.assertTrue('x' in lower)

    def test_keys(self):
        """ Tests to ensure 2 contexts that contain overlapping sets of keys
            appear to have one set of keys where each key is unique (i.e. a 'set')
        """

        d1 = DataContext(name='d1',subcontext={'a':1,'b':2})
        d2 = DataContext(name='d2',subcontext={'a':3,'c':4})
        m = MultiContext(d1, d2, name='m')

        sorted_keys = sorted(m.keys())
        self.assertEqual(sorted_keys, ['a', 'b', 'c'])

    def test_contexts_list_changes(self):
        """ Checking if change in items in contexts updates the multi-context
        """
        d1 = DataContext(name = 'test_context1',
                         subcontext = {'a':1, 'b':2})
        d2 = DataContext(name = 'test_context2')

        m = MultiContext(*[d1,d2], **{'name': 'test_mc'})
        self.assertTrue(len(list(m.keys())) == 2)

        # Add another context
        d3 = DataContext(name = 'test_context3',
                         subcontext = {'c':3, 'd':4})
        m.subcontexts.append(d3)
        self.assertTrue(len(list(m.keys())) == 4)

        # Modify an existing context
        m.subcontexts[1].subcontext = {'cc': 5}
        self.assertTrue(len(list(m.keys())) == 5)

        # Remove a context
        m.subcontexts.pop(0)
        self.assertTrue(len(list(m.keys())) == 3)


def test_persistence():
    """ Checking if the data persists correctly when saving and loading back
    """
    d1 = DataContext(name = 'test_context1',
                     subcontext = {'a':1, 'b':2})
    d2 = DataContext(name = 'test_context2',
                     subcontext = {'foo':100, 'bar':200, 'baz':300})
    m = MultiContext(d1, d2, name='test_mc')

    f = BytesIO()
    m.save(f)
    f.seek(0, 0)
    new_m = MultiContext.load(f)

    assert m.name == new_m.name

    # Test keys of new_m
    assert set(new_m.keys()) == set(m.keys())

    # Check values
    assert new_m['a'] == m['a']
    assert new_m['b'] == m['b']
    assert new_m['foo'] == m['foo']
    assert new_m['bar'] == m['bar']

    # Check contexts
    assert new_m.subcontexts == m.subcontexts


def test_checkpoint():
    d1 = DataContext()
    d1['a'] = object()
    d2 = DataContext()
    d2['b'] = object()
    m = MultiContext(d1, d2)
    copy = m.checkpoint()
    assert copy is not m
    assert copy.subcontexts is not m.subcontexts
    assert len(copy.subcontexts) == len(m.subcontexts)
    for csc, msc in zip(copy.subcontexts, m.subcontexts):
        assert csc is not msc
        assert set(csc.keys()) == set(msc.keys())
        for key in msc.keys():
            assert csc[key] is msc[key]

    assert set(copy.keys()) == set(m.keys())
    assert copy['a'] is m['a']
    assert copy['b'] is m['b']


def test_checkpoint_nested():
    d1 = DataContext()
    d1['a'] = object()
    d2 = DataContext()
    d2['b'] = object()
    m1 = MultiContext(d1, d2)
    m = MultiContext(m1)
    copy = m.checkpoint()
    assert copy is not m
    assert copy.subcontexts is not m.subcontexts
    assert len(copy.subcontexts) == len(m.subcontexts)
    csc1 = copy.subcontexts[0]
    msc1 = m.subcontexts[0]
    for csc, msc in zip(csc1.subcontexts, msc1.subcontexts):
        assert csc is not msc
        assert set(csc.keys()) == set(msc.keys())
        for key in msc.keys():
            assert csc[key] is msc[key]

    assert set(copy.keys()) == set(m.keys())
    assert copy['a'] is m['a']
    assert copy['b'] is m['b']



