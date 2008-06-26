# Standard library imports
import os, unittest

# Major library imports
from numpy import arange, zeros
from numpy.testing import assert_array_equal

# ETS imports
from enthought.contexts.adapted_data_context import AdaptedDataContext
from enthought.contexts.with_mask_adapter import WithMaskAdapter
from enthought.contexts.data_context import DataContext


class WithMaskAdapterTestCase(unittest.TestCase):

    def setUp(self):
        dc = DataContext(name='dc')
        dc['depth'] = arange(0., 10000., 1000.)
        self.context = dc

    #---------------------------------------------------------------------------
    # WithTestCase interface
    #---------------------------------------------------------------------------

    def test_floats_to_arrays(self):
        """ Assigning floats to arrays
        """
        dc = self.context
        depth = dc['depth']
        dc['vp'] = zeros(depth.shape)
        dc['vs'] = zeros(depth.shape)
        mask = (depth<4000.0) & (depth > 1000.0)
        adc = AdaptedDataContext(subcontext=self.context,
            _adapters=[WithMaskAdapter(mask=mask)])
        adc['vp'] = 1.0
        adc['vs'] = 1.5

        depth = arange(0., 10000., 1000.)
        desired_vp = zeros(depth.shape)
        desired_vs = zeros(depth.shape)
        desired_vp[(depth<4000.0) & (depth > 1000.0)] = 1.0
        desired_vs[(depth<4000.0) & (depth > 1000.0)] = 1.5

        assert_array_equal(desired_vp, dc['vp'])
        assert_array_equal(desired_vs, dc['vs'])

    def test_different_sized_arrays(self):
        """ Different sized arrays
        """

        dc = self.context
        depth = dc['depth']
        dc['vp'] = zeros(5)
        dc['vs'] = zeros(5)
        mask = (depth<4000.0) & (depth > 1000.0)
        adc = AdaptedDataContext(subcontext=self.context,
            _adapters=[WithMaskAdapter(mask=mask)])
        adc['vp'] = 1.0
        adc['vs'] = 1.5

        depth = arange(0., 10000., 1000.)
        desired_vp = zeros(depth.shape)
        desired_vs = zeros(depth.shape)
        desired_vp[(depth<4000.0) & (depth > 1000.0)] = 1.0
        desired_vs[(depth<4000.0) & (depth > 1000.0)] = 1.5

        assert_array_equal(desired_vp, dc['vp'])
        assert_array_equal(desired_vs, dc['vs'])

    def test_same_size_array(self):
        """ Same sized array assignments.
        """

        dc = self.context
        depth = dc['depth']
        dc['vp'] = zeros(depth.shape)
        dc['vs'] = zeros(depth.shape)
        mask = (depth<4000.0) & (depth > 1000.0)
        adc = AdaptedDataContext(subcontext=self.context,
            _adapters=[WithMaskAdapter(mask=mask)])
        adc['vp'] = arange(0., 10., 1.)
        adc['vs'] = arange(0., 100., 10.)

        desired_vp = arange(0., 10., 1.0)
        desired_vs = arange(0., 100., 10.)

        assert_array_equal(desired_vp, dc['vp'])
        assert_array_equal(desired_vs, dc['vs'])

