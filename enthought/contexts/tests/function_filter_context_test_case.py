# Standard library imports
import unittest

# Geo library imports
from enthought.contexts.function_filter_context import FunctionFilterContext
from enthought.block_canvas.debug.my_operator import add, mul, div, sub

class FunctionFilterContextTestCase(unittest.TestCase):
    """ Test whether the context filters values by their type appropriately.

        Note: We can't run all the AbstractContextTestCases on this class
              because it is picky about what variables it allows to be
              assigned into it, and many of the tests will fail.
    """

    #---------------------------------------------------------------------------
    # TestCase interface
    #---------------------------------------------------------------------------

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    #---------------------------------------------------------------------------
    # FunctionFilterContextTestCase interface
    #---------------------------------------------------------------------------

    def test_allows(self):
        """ Does the allow method filter names appropriately?
        """
        context = FunctionFilterContext(name = 'functionfilter')

        self.assertTrue(context.allows(add, 'add'))
        self.assertFalse(context.allows('a', 'var_name'))
        self.assertFalse(context.allows(1, 'var_name'))


    def test_set_allowed_name(self):
        """ Does the context accept names that aren't in its name list?
        """
        context = FunctionFilterContext(name='functionfilter')

        context['add'] = add
        self.assertEqual(context['add'], add)


### EOF ------------------------------------------------------------------------
