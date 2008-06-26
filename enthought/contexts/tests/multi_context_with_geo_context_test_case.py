# Standard Library Imports
import unittest
import timeit

from numpy import array

# Geo Library imports
from enthought.contexts.tests.multi_context_test_case import MultiContextTestCase
from enthought.contexts.api import MultiContext, GeoContext

class MultiContextWithGeoContextTestCase(MultiContextTestCase):
    """ Test a MultiContext with a GeoContext at the top.

        The GeoContext only accepts ndarray and Log objects which results in
        new behavior over a standard GeoContext that needs to be tested.
    """

    ############################################################################
    # AbstactContextTestCase interface
    ############################################################################

    def context_factory(self):
        """ Return the type of context we are testing.
        """
        return MultiContext(GeoContext(), {})

    def matched_input_output_pair(self):
        """ Return values for testing dictionary get/set, etc.
        """
        return array((1,2,3)), array((1,2,3))


if __name__ == '__main__':
    import sys
    unittest.main(argv=sys.argv)
