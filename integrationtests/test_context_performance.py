from __future__ import print_function

# Standard library imports
import unittest
import timeit

# Enthought library imports
from traits.testing.api import performance
from codetools.contexts.tests.abstract_context_test_case import AbstractContextTestCase
from codetools.contexts.data_context import DataContext
from codetools.contexts.multi_context import MultiContext
from codetools.contexts.api import AdaptedDataContext

##########################################################################
#
#  These tests used to be in:
#
#  enthought/contexts/tests/
#
#                      data_context_test_case.py
#                      multi_context_test_case.py
#                      context_with_unit_conversion_adapter_test_case.py


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
        this_setup = "from codetools.contexts.data_context import DataContext\n" \
                     "context=DataContext()\n" \
                     "context['vp'] = vp\n"
        context_setup = setup + this_setup + compiled_setup
        context_expr = "eval(compiled_expr, globals(), context)"
        context_timer = timeit.Timer(context_expr, context_setup)
        context_res = context_timer.timeit(N)


        slowdown = context_res/std_res
        msg = 'actual slowdown: %f\nallowed slowdown: %f' % (slowdown, allowed_slowdown)
        assert slowdown < allowed_slowdown, msg


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

    @performance
    def test_eval_is_not_slow(self):
        """ eval() with DataContext is the speed of a dict. (slowdown < 1.3)

            This is test using a vp array with 20 values in it to try and get
            a reasonable use case.
        """

        ### Parameters #########################################################

        # Slowdown we will allow compared to standard python evaluation
        allowed_slowdown = 1.5

        # Number of timer iterations.
        N = 10000

        ### Standard execution #################################################
        setup = "from numpy import arange\n" \
                "vp=arange(20.)\n"
        expr = 'vp+vp+vp+vp+vp+vp'
        std = timeit.Timer(expr, setup)
        std_res = std.timeit(N)

        ### Eval execution #####################################################
        # Note: This is not used, but it is here for reference
        #
        # eval is actually slower (by an order or so of magnitude for single
        # numbers) than a simple expression.  But for our array, it should be
        # about the same speed.
        compiled_setup = "compiled_expr = compile(%r,'expr','eval')\n" % expr
        eval_setup = setup + compiled_setup
        eval_expr = "eval(compiled_expr)"
        eval_timer = timeit.Timer(eval_expr, eval_setup)
        eval_res = eval_timer.timeit(N)

        ### DataContext execution ##############################################
        this_setup = "from codetools.contexts.api import MultiContext\n" \
                     "context=MultiContext()\n" \
                     "context['vp'] = vp\n"
        context_setup = setup + this_setup + compiled_setup
        context_expr = "eval(compiled_expr, globals(), context)"
        context_timer = timeit.Timer(context_expr, context_setup)
        context_res = eval_timer.timeit(N)

        slowdown = context_res/std_res
        msg = 'actual slowdown: %f' % slowdown
        assert slowdown < allowed_slowdown, msg


class UnitConversionContextAdapterTestCase(unittest.TestCase):
    """ Other tests for UnitConversionContextAdapater
    """

    ############################################################################
    # TestCase interface
    ############################################################################

    def setUp(self):
        self.context = AdaptedDataContext(context=DataContext())

    @performance
    def test_exec_is_not_slow(self):
        """ Compare exec with Adapter to the speed of a dict. (slowdown < 2.5)

            This test compares the costs of unit converting 1000 data points
            using pure python and then using our adapater code.  A factor of
            2.5 is pretty lousy I'd say, so we don't want to do this much.
            At the edge of function boundaries is OK.
        """

        ### Parameters ########################################################

        # Slowdown we will allow compared to standard python evaluation
        allowed_slowdown = 2.5

        # Number of timer iterations.
        N = 1000

        ### Standard execution ################################################
        setup = "from numpy import arange\n" \
                "from scimath.units.length import meters, feet\n" \
                "from scimath import units\n" \
                "depth_meters = arange(1000)\n"
        code = "depth_feet = units.convert(depth_meters, meters, feet)\n" \
               "depth2_feet = depth_feet + depth_feet\n" \
               "depth2_meters = units.convert(depth2_feet, feet, meters)\n"
        std = timeit.Timer(code, setup)
        std_res = std.timeit(N)

        ### Adapter execution #################################################
        # Adapter is set up to convert depth meters->feet and
        # depth2 feet->meters
        setup = "from numpy import arange\n" \
                "from scimath.units.length import meters, feet\n" \
                "from codetools.contexts.api import DataContext, AdaptedDataContext\n" \
                "from scimath.units.api import UnitArray\n" \
                "from codetools.contexts.api import UnitConversionAdapter\n" \
                "data_context = DataContext()\n" \
                "context = AdaptedDataContext(context=data_context)\n" \
                "adapter = UnitConversionAdapter(getitem_units={'depth':feet, 'depth2':meters})\n" \
                "context.push_adapter(adapter)\n" \
                "context['depth'] = UnitArray(arange(1000),units=meters)\n" \
                "compiled = compile('depth2 = depth + depth','foo','exec')\n"

        code = "exec(compiled, globals(), context)\n"
        adp = timeit.Timer(code, setup)
        adp_res = adp.timeit(N)

        slowdown = adp_res/std_res
        msg = 'actual slowdown, time: %f' % slowdown, adp_res/N
        print("[actual slowdown=%3.2f]  " % slowdown)
        assert slowdown < allowed_slowdown, msg


if __name__ == '__main__':
    unittest.main()
