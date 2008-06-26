# Standard libary imports
import unittest

# Geo Library imports
from enthought.contexts.api import (AdaptedDataContext, DataContext,
                                                NameAdapter)


class NameAdapterTestCase(unittest.TestCase):

    ###########################################################################
    # TestCase interface
    ###########################################################################

    def setUp(self):
        unittest.TestCase.setUp(self)

        # Create the contexts
        self.context = AdaptedDataContext(subcontext=DataContext())
        self.raw_context = self.context.subcontext

        # Add data (before creating the adapter)
        self.context.update(fun=1, bar=2, baz=3, not_mapped=4)

        # Add an adapter
        self.adapter = NameAdapter(map={"foo":"fun", "bar":"baz"})
        self.context.push_adapter(self.adapter)

    def tearDown(self):
        unittest.TestCase.tearDown(self)


    ###########################################################################
    # MaskingAdapterTestCase interface
    ###########################################################################

    def test_adapt_name(self):
        """ Does adapter map values correctly?
        """

        name = self.adapter.adapt_name(self.raw_context, 'foo')
        self.assertEqual(name, 'fun')
        self.assertEqual(self.raw_context[name], 1)

    def test_adapt_name_existing_value(self):
        """ Does adapter not map values that are in the context?
        """

        name = self.adapter.adapt_name(self.raw_context, 'bar')
        self.assertEqual(name, 'bar')
        self.assertEqual(self.raw_context[name], 2)

    def test_adapt_name_not_in_map(self):
        """ Does adapter work for values not in the map?
        """

        name = self.adapter.adapt_name(self.raw_context, 'not_mapped')
        self.assertEqual(name, 'not_mapped')
        self.assertEqual(self.raw_context[name], 4)


if __name__ == '__main__':
    import sys
    unittest.main(argv=sys.argv)
