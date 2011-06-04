# Standard Library Imports
import sys
import unittest

# Third Party Libary imports
import nose

# Numeric Libary imports
from numpy import all

# Enthought Library imports
from scimath.units.length import meters, feet
from scimath.units.time import second

# ETS Library imports
from scimath.units.api import UnitArray

# Geo Library imports
from codetools.contexts.api import DataContext, AdaptedDataContext
from codetools.contexts.adapter.unit_conversion_adapter import UnitConversionAdapter

# Test imports
from codetools.contexts.tests.data_context_test_case import DataContextTestCase

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

    def _simple_eval_works(self, context, key_name, input, output):
        """ A Context should work as an evaluation context Python's eval()

            Note: depending how your adapters work, this will likely need to
                  be over-ridden.
        """
        context[key_name] = input
        expr = '%s + %s' % (key_name, key_name)
        result = eval(expr, globals(), context)
        self.failUnlessEqual(result, context[key_name]+context[key_name])


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


if __name__ == '__main__':
    import sys
    unittest.main(argv=sys.argv)
