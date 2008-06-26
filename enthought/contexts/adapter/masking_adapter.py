""" Mask values going in and out of a context.
"""

# Standard library imports
from copy import copy
from numpy import NaN, array, empty, float64, iscomplex, isreal, ndarray

# Enthought library imports
from enthought.traits.api import Any, HasTraits

# Local imports
from i_adapter import IAdapter

# TODO Generalize to any slice object (eventually)

class MaskingAdapter(HasTraits):
    """ Apply a mask to values in a context that are compatible.
    """

    __implements__ = [IAdapter]

    ###########################################################################
    # UnitConversionContextAdapter traits
    ###########################################################################

    # Mask used to filter values as they pass through
    mask = Any

    ###########################################################################
    # Public IAdapter interface.
    ###########################################################################

    def adapt_getitem(self, context, name, value):
        """ Return region in 'value' that fits our mask.
        """

        # FIXME This only work if self.mask and value have the same size. (We
        # run into this problem when we try to nest masking adapters.)

        # Mask anything we can, pass-through everything else
        try:
            return name, value[self.mask]
        except TypeError:
            return name, value

    def adapt_setitem(self, context, name, value):
        """ Modify 'value' so that it only affects the masked region of 'name'.
        """

        # Do we cooperate with unit adapters? In the first branch, we grab
        # some data from 'name', stick it in 'value', and pass it on. Does this
        # cause problems...?

        # TODO This belongs somewhere else. And it's awkward.
        def get_default_value_and_dtype(name, value):

            if isinstance(value, ndarray):
                value = value.dtype.type()
            elif isinstance(value, tuple):
                value = value[0]

            if isreal(value) or iscomplex(value):
                return NaN, float64
            elif isinstance(value, str):
                return 'unknown', object
            elif isinstance(value, bool):
                return False, bool

        # TODO How do these chain: with masking adapters? with unit adapters?
        #  - Masking adapters: poorly.
        #  - Unit adapters: poorly when they are below us.
        if name in context:
            # Make a value that updates just the masked part of 'context[name]'
            new = copy(context[name])
            ###new[self.mask] = value
            ###return name, new
            # FIXME new.units given by context[name].units since we bypass any
            # unit adapters below us. However, units aren't our concern, so we
            # need a richer composing abstraction...
        else:
            # Expand 'value' to "fit" the shape defined by 'context'
            default_value, dtype = get_default_value_and_dtype(name, value)
            new = self._empty_of_local_shape(context, dtype=dtype)
            new.fill(default_value)
            ###new[self.mask] = value
            ###return name, new

        try:
            new[self.mask] = value
            return name, new
        except TypeError:
            # FIXME Do we return new? value? something else?
            return name, new

    # TODO What policy do we want here?
    def _empty_of_local_shape(self, context, dtype):
        """ Create an empty array whose shape matches its environment.

            This kind of behavior is necessary because we allow new bindings to
            be created through masking adapters and need to create a shape for
            the real, unmasked array. The current behavior is to assume a
            'depth' array exists and to use its shape. FIXME
        """
        assert 'depth' in context
        return empty(shape=context['depth'].shape, dtype=dtype)
