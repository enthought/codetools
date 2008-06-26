
# Standard Library Imports
from cStringIO import StringIO
import timeit

import nose

from enthought.testing.api import performance

# Local library imports
from enthought.contexts.data_context import DataContext
from enthought.contexts.tests.abstract_context_test_case import AbstractContextTestCase


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

    @performance
    def test_eval_is_not_slow(self):
        """ eval() with DataContext is the speed of a dict. (slowdown < 2.0)

            This is test using a vp array with 20 values in it to try and get
            a reasonable use case.
        """

        ### Parameters ########################################################

        # Slowdown we will allow compared to standard python evaluation
        allowed_slowdown = 2.0

        # Number of timer iterations.
        N = 10000

        ### Standard execution ################################################
        setup = "from numpy import arange\n" \
                "vp=arange(20.)\n"
        expr = 'vp+vp+vp+vp+vp+vp'
        std = timeit.Timer(expr, setup)
        std_res = std.timeit(N)

        ### Eval execution ####################################################
        # Note: This is not used, but it is here for reference
        #
        # eval is actually slower (by an order or so of magnitude for single
        # numbers) than a simple expression.  But for our array, it should be
        # about the same speed.
        compiled_setup = "compiled_expr = compile('%s','expr','eval')\n" % expr
        eval_setup = setup + compiled_setup
        eval_expr = "eval(compiled_expr)"
        eval_timer = timeit.Timer(eval_expr, eval_setup)
        eval_res = eval_timer.timeit(N)

        ### DataContext execution #############################################
        this_setup = "from enthought.contexts.data_context import DataContext\n" \
                     "context=DataContext()\n" \
                     "context['vp'] = vp\n"
        context_setup = setup + this_setup + compiled_setup
        context_expr = "eval(compiled_expr, globals(), context)"
        context_timer = timeit.Timer(context_expr, context_setup)
        context_res = context_timer.timeit(N)


        slowdown = context_res/std_res
        msg = 'actual slowdown: %f\nallowed slowdown: %f' % (slowdown, allowed_slowdown)
        assert slowdown < allowed_slowdown, msg


    


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

