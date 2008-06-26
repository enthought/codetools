# Standard libary imports
import unittest

# Numeric libary imprts
from numpy import array

# Enthought library imports
from enthought.units.length import meters

# Geo library imports
from enthought.contexts.api import UnitApplyAdapter

class UnitApplyAdapterTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_discovers_units(self):
        getitem_units = {'depth': meters}
        adapter = UnitApplyAdapter(getitem_units=getitem_units)
        name, value = adapter.adapt_getitem(None, 'depth', array((1,2,3)))
        self.assertEqual(value.units,meters)


if __name__ == '__main__':
    unittest.main()