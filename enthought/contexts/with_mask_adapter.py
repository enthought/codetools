# Standard imports
from numpy import ndarray, ones, NaN

# Enthought library imports
from enthought.traits.api import Any, HasTraits

# Local imports
from adapter.i_adapter import IAdapter

# TODO Generalize to any slice object (eventually)

class WithMaskAdapter(HasTraits):
    """ Apply a mask to values in a context that are compatible.
    """

    __implements__ = [IAdapter]
    mask = Any


    def __init__(self, mask, **traits):
        """ If mask is not an array, ensure it is an array
        """

        if isinstance(mask, ndarray):
            self.mask = mask
        else:
            self.mask = ndarray([mask])
        super(WithMaskAdapter, self).__init__(**traits)


    def _create_array(self, mask_value, default_value=NaN):
        """ Create an array with given fill_(default_)value and mask_value.
        """

        value = default_value*ones(self.mask.shape)
        value[self.mask] = mask_value
        return value


    def adapt_getitem(self, context, name, value):
        """ Get item from context
        """

#        # FIXME: This doesn't work correctly always.
#        result = None
#        if isinstance(value,ndarray) and value.shape == self.mask.shape:
#            result = value[self.mask]
#        else:
#            result = value
#        return result

        return name, value


    def adapt_setitem(self, context, name, value):
        """ Set item in context
        """

        # Condition for keeping the old array value
        cond_keep_array = context.has_key(name) and \
                             isinstance(context[name], ndarray) and \
                             context[name].shape == self.mask.shape

        if cond_keep_array:
            # Check if the new value is the same length as the mask
            if isinstance(value, ndarray) and value.shape == self.mask.shape:
                context[name][:] = value

            # If the new value is a singleton that has to be applied to the
            # masked values alone.
            elif type(value) in [float, int, str, unicode]:
                context[name][self.mask] = value

            return name, context[name]
        else:
            if context.has_key(name):
                old_value = context[name]
                if isinstance(old_value, ndarray):
                    old_value = old_value[0]
            else:
                old_value = NaN

            return name, self._create_array(value, old_value)


### EOF ------------------------------------------------------------------------
