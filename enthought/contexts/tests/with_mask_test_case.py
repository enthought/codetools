""" Test cases for with_mask
"""

# Standard library imports
import os, unittest

# Major library imports
from numpy import arange, zeros

# ETS imports
from enthought.contexts.with_mask import Mask
from enthought.contexts.data_context import DataContext
from enthought.blocks.api import Block


class WithMaskTestCase(unittest.TestCase):
    """ Test whether the masking works with 'with' statement.
    """

    #---------------------------------------------------------------------------
    # TestCase interface
    #---------------------------------------------------------------------------

    def setUp(self):
        unittest.TestCase.setUp(self)
        dc = DataContext(name='dc')
        self.context = DataContext(subcontext=dc)
        dc['depth'] = arange(0.,10000., 1000.)
        self.context['context'] = dc.subcontext
        self.code_dir = os.path.join(os.path.dirname(__file__),
                                     'with_mask_codes')

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    #---------------------------------------------------------------------------
    # WithTestCase interface
    #---------------------------------------------------------------------------

    def test1(self):
        """ Assigning floats to arrays
        """

        file_object = open(os.path.join(self.code_dir,'test1.py'), 'r')
        code = file_object.read()
        file_object.close()

        b = Block(code)
        b.execute(self.context)

        depth = arange(0., 10000., 1000.)
        desired_vp = zeros(depth.shape)
        desired_vs = zeros(depth.shape)
        desired_vp[(depth<4000.0) & (depth > 1000.0)] = 1.0
        desired_vs[(depth<4000.0) & (depth > 1000.0)] = 1.5

        # Check equal
        self.assertTrue((desired_vp == self.context['vp']).all())
        self.assertTrue((desired_vs == self.context['vs']).all())


    def test2(self):
        """ Different sized arrays
        """

        file_object = open(os.path.join(self.code_dir,'test2.py'), 'r')
        code = file_object.read()
        file_object.close()

        b = Block(code)
        b.execute(self.context)

        depth = arange(0., 10000., 1000.)
        desired_vp = zeros(depth.shape)
        desired_vs = zeros(depth.shape)
        desired_vp[(depth<4000.0) & (depth > 1000.0)] = 1.0
        desired_vs[(depth<4000.0) & (depth > 1000.0)] = 1.5

        # Check equal
        self.assertTrue((desired_vp == self.context['vp']).all())
        self.assertTrue((desired_vs == self.context['vs']).all())


    def test3(self):
        """ Same sized array assignments within 'with' block
        """

        file_object = open(os.path.join(self.code_dir,'test3.py'), 'r')
        code = file_object.read()
        file_object.close()

        b = Block(code)
        b.execute(self.context)

        desired_vp = arange(0., 10., 1.)
        desired_vs = arange(0., 100., 10.)

        # Check equal
        self.assertTrue((desired_vp == self.context['vp']).all())
        self.assertTrue((desired_vs == self.context['vs']).all())



if __name__ == "__main__":
    import sys
    unittest.main(argv=sys.argv)

### EOF ------------------------------------------------------------------------
