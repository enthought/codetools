# Standard libary imports
import unittest

# Numeric libary imports
from numpy import all, array, isnan, linspace, nan

# Geo Library imports
from enthought.contexts.api import AdaptedDataContext, DataContext, MaskingAdapter


class MaskingAdapterTestCase(unittest.TestCase):

    ###########################################################################
    # TestCase interface
    ###########################################################################

    def setUp(self):

        unittest.TestCase.setUp(self)

        # Set up data for the contexts
        depth = linspace(0.0,100.0, 11)
        lith = array(['sand']*len(depth), dtype=object)

        # Create the contexts
        self.context = AdaptedDataContext(subcontext=DataContext())
        self.raw_context = self.context.subcontext

        # Add data (before creating the adapter)
        self.context.update(depth=depth, lith=lith)

        # Add an adapter
        self.mask = (20.0<=depth) & (depth<=50.0)
        self.adapter = MaskingAdapter(mask=self.mask)
        self.context.push_adapter(self.adapter)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    ###########################################################################
    # MaskingAdapterTestCase interface
    ###########################################################################

    def test_getitem(self):
        """ Does adapter mask values correctly?
        """
        name, value = self.adapter.adapt_getitem(self.raw_context, 'depth',
                                                 self.raw_context['depth'])
        self.assertEqual(len(value), 4)
        self.assertTrue(all(value==(20.0, 30.0, 40.0, 50.0)))

    def test_setitem_existing_value(self):
        """ Does setitem on existing data only change the masked values?
        """
        new_values = (30.0, 40.0, 50.0, 60.0)

        desired = self.raw_context['depth'].copy()
        desired[self.mask] = new_values

        name, value = self.adapter.adapt_setitem(self.raw_context, 'depth',
                                                 new_values)
        self.assertEqual(len(value), 11)
        self.assertTrue(all(value==desired))

    def test_setitem_non_existing_value(self):
        """ Does setitem on non-existing data expand to depth's shape?
        """
        new_values = (30.0, 40.0, 50.0, 60.0)

        desired = self.raw_context['depth'].copy()
        desired[self.mask] = new_values
        desired[~self.mask] = nan

        name, value = self.adapter.adapt_setitem(self.raw_context, 'foo',
                                                 new_values)

        self.assertEqual(len(value), len(desired))
        self.assertTrue(all((value==desired) | (isnan(value)==isnan(desired))))

    def test_context_getitem(self):
        """ Are the returned values from context masked correctly?
        """
        depth = self.context['depth']
        self.assertEqual(len(depth), 4)
        self.assertTrue(all(depth==(20.0, 30.0, 40.0, 50.0)))

    def test_context_setitem_existing(self):
        """ Are the returned values from context masked correctly?
        """
        new_values = (30.0, 40.0, 50.0, 60.0)
        self.context['depth'] = new_values

        # Grab the values from the underlying context, skipping the mask.
        depth = self.raw_context['depth']

        desired = self.raw_context['depth'].copy()
        desired[self.mask] = new_values
        self.assertTrue(all(depth==desired))

if __name__ == '__main__':
    import sys
    unittest.main(argv=sys.argv)
