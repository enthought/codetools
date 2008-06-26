# Standard Library Imports
import unittest
import timeit

# Numeric Libary imports
from numpy import all

# Enthought Library imports
from enthought.testing.api import performance
from enthought.units.length import meters, feet
from enthought.units.time import second

# ETS Library imports
from enthought.numerical_modeling.units.api import UnitArray

# Geo Library imports
from enthought.contexts.api import DataContext, AdaptedDataContext
from enthought.contexts.adapter.unit_conversion_adapter import UnitConversionAdapter

# Test imports
from enthought.contexts.tests.data_context_test_case import DataContextTestCase

class ContextWithUnitConversionAdapterLogTestCase(DataContextTestCase):
    """ Test whether context still works with an adapter attached.

        This doesn't test any conversion behavior.
    """

    ############################################################################
    # AbstractContextTestCase interface
    ############################################################################

    def context_factory(self):
        """ Return the type of context we are testing.
        """
        data_context=DataContext()
        context = AdaptedDataContext(context=data_context)
        name = self.key_name()
        getitem_units = {name:meters/second}
        adapter = UnitConversionAdapter(getitem_units=getitem_units)
        context.push_adapter(adapter)
        return context

    def key_name(self):
        return 'vp'

    def matched_input_output_pair(self):
        """ Return values for testing dictionary get/set, etc.
        """
        input = UnitArray((1,2,3),units=meters/second)
        output = UnitArray((1,2,3),units=meters/second)
        return input, output

    def unmatched_pair(self):
        """ Return values for testing dictionary get/set, etc.
        """
        input = UnitArray((1,2,3),units=meters/second)
        output = UnitArray((4,5,6),units=meters/second)
        return input, output


class UnitConversionContextAdapterTestCase(unittest.TestCase):
    """ Other tests for UnitConversionContextAdapater
    """

    ############################################################################
    # TestCase interface
    ############################################################################

    def setUp(self):
        self.context = AdaptedDataContext(context=DataContext())

    ############################################################################
    # UnitConversionContextAdapterTestCase interface
    ############################################################################

    def test_getitem_converts_correctly(self):
        """ Does getitem convert units correctly?
        """
        getitem_units = {'depth':feet}
        adapter = UnitConversionAdapter(getitem_units=getitem_units)

        old_log = UnitArray((1,2,3),units=meters)

        self.context['depth'] = old_log
        self.context.push_adapter(adapter)

        new_log = self.context['depth']

        # Did the values get converted correctly?
        self.assert_(all(new_log==old_log.as_units(feet)))

        # Are the units assigned correctly?
        self.assert_(new_log.units==feet)

        return

    def test_setitem_converts_correctly(self):
        """ Does setitem convert units correctly?
        """

        old_log = UnitArray((1,2,3),units=meters)
        getitem_units = {'depth':feet}
        adapter = UnitConversionAdapter(getitem_units=getitem_units)

        self.context.push_adapter(adapter)

        # pass the log into the conversion adapter as meters
        self.context['depth'] = old_log

        # Now retreive the log from the underlying context.
        new_log = self.context['depth']

        # Did the values get converted correctly?
        self.assert_(all(new_log==old_log.as_units(feet)))

        # Are the units assigned correctly?
        self.assert_(new_log.units==feet)

        return

    @performance
    def test_exec_is_not_slow(self):
        """ Compare exec with Adapter to the speed of a dict. (slowdown < 2.0)

            This test compares the costs of unit converting 1000 data points
            using pure python and then using our adapater code.  A factor of
            2.0 is pretty lousy I'd say, so we don't want to do this much.
            At the edge of function boundaries is OK.
        """

        ### Parameters ########################################################

        # Slowdown we will allow compared to standard python evaluation
        allowed_slowdown = 2.0

        # Number of timer iterations.
        N = 1

        ### Standard execution ################################################
        setup = "from numpy import arange\n" \
                "from enthought.units.length import meters, feet\n" \
                "from enthought import units\n" \
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
                "from enthought.units.length import meters, feet\n" \
                "from enthought.contexts.api import DataContext, AdaptedDataContext\n" \
                "from enthought.numerical_modeling.units.api import UnitArray\n" \
                "from enthought.contexts.api import UnitConversionAdapter\n" \
                "data_context = DataContext()\n" \
                "context = AdaptedDataContext(context=data_context)\n" \
                "adapter = UnitConversionAdapter(getitem_units={'depth':feet, 'depth2':meters})\n" \
                "context.push_adapter(adapter)\n" \
                "context['depth'] = UnitArray(arange(1000),units=meters)\n" \
                "compiled = compile('depth2 = depth + depth','foo','exec')\n"

        code = "exec compiled in globals(), context\n"
        adp = timeit.Timer(code, setup)
        adp_res = adp.timeit(N)


        slowdown = adp_res/std_res
        msg = 'actual slowdown, time: %f' % slowdown, adp_res/N
        print "[actual slowdown=%3.2f]  " % slowdown,
        assert slowdown < allowed_slowdown, msg

if __name__ == '__main__':
    import sys
    unittest.main(argv=sys.argv)
