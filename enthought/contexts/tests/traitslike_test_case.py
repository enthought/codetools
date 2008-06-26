from enthought.traits.api import Int, Float

from enthought.contexts.data_context import DataContext
from enthought.contexts.traitslike_context_wrapper import TraitslikeContextWrapper


def remove_known_traits(trait_names):
    """ Remove the irrelevant trait names from a list of trait names in order to
    get to the useful trait names.

    Also, sort the list for ease of use in testing.
    """
    return sorted([x for x in trait_names 
        if x not in ('_context', '_synched', 'trait_added', 'trait_modified')])


class TestTraitslike(object):
    def setup(self):
        d = DataContext()
        d['a'] = 1
        d['b'] = 2.0
        tcw = TraitslikeContextWrapper(_context=d)
        tcw.add_traits('c', a=Int, b=Float)

        self.d = d
        self.tcw = tcw

    def test_add_traits(self):
        """ Does adding traits work?
        """
        tcw = TraitslikeContextWrapper(_context=self.d)
        assert remove_known_traits(tcw.trait_names()) == []
        tcw.add_traits(a=Int)
        assert remove_known_traits(tcw.trait_names()) == ['a']
        tcw.add_traits(b=Float)
        assert remove_known_traits(tcw.trait_names()) == ['a', 'b']
        tcw.add_traits('c')
        assert remove_known_traits(tcw.trait_names()) == ['a', 'b', 'c']

    def test_add_several_traits(self):
        """ Does adding multiple traits at a time work?
        """
        assert remove_known_traits(self.tcw.trait_names()) == ['a', 'b', 'c']

    def test_initial_values_from_context(self):
        """ Are the initial values propagated from the context to the traits
        correctly?
        """
        assert self.tcw.a == 1
        assert self.tcw.b == 2.0

    def test_initial_values_from_traits(self):
        """ Are the initial values propagated from the traits to the context correctly?
        """
        tcw = TraitslikeContextWrapper(_context=self.d)
        tcw.add_traits(d=Int)
        assert tcw.d == 0
        assert tcw._context['d'] == 0
        tcw.add_traits('e')
        assert tcw.e is None
        assert tcw._context['e'] is None

    def test_synch(self):
        """ Does synching work?
        """
        self.tcw.a = 2
        assert self.tcw._context['a'] == 2

        self.tcw._context['b'] = 3.0
        assert self.tcw.b == 3.0

    def test_synch_off(self):
        """ Can synching be turned off?
        """
        self.tcw._synched = False
        self.tcw.a = 2
        assert self.tcw._context['a'] == 1


