#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

# Enthought imports
from traits.api import HasTraits, List

# Local imports
from .i_adapter_manager import IAdapterManager


class AdapterManagerMixin(IAdapterManager):
    """ Handles management of an adapter stack for objects that implement
        IContext.
    """

    ### Private AdapterManagerMixin traits #####################################

    # List of adapters that modify the values of the context.
    # This is treated like a stack with the values at the front of the list
    # closest to the context data.
    _adapters = List


    ############################################################################
    # IAdapterManager public interface
    ############################################################################

    def push_adapter(self, adapter):
        """ Add an adapter to the 'top' of the adapter stack.
        """
        return self._adapters.append(adapter)

    def pop_adapter(self):
        """ Remove the 'top' from the top of the adapter stack.

            fixme: How to handle if the stack is empty?
        """
        return self._adapters.pop()


    ### Private AdapterMangerMixin interface ###################################

    def _adapt_name(self, context, name):
        """ Apply adapters in order, calling their adapt_name method.
        """
        # Call adapt_name for each adapter.  The output of each adapter becomes
        # the input for the next adapter.
        for adapter in self._adapters[::-1]:
            if hasattr(adapter, "adapt_name"):
                name = adapter.adapt_name(context, name)

        return name

    def _adapt_getitem(self, context, name, value):
        """ Apply adapters in order, calling their adapt_getitem() method.
        """
        # Call get_item for each adapter.  The output of each adapter becomes
        # the input for the next adapter.
        for adapter in self._adapters:
            # E.g: a simple NameAdapter need not declare its own adapt_getitem
            if hasattr(adapter, "adapt_getitem"):
                name, value = adapter.adapt_getitem(context, name, value)

        return name, value

    def _adapt_setitem(self, context, name, value):
        """ Apply dapters in reverse order, calling their adapt_setitem()
            method.
        """
        # Call set_item for each adapter in reverse order.  The output of each
        # adapter becomes the input for the next adapter.
        for adapter in self._adapters[::-1]:
            # E.g: a simple NameAdapter need not declare its own adapt_setitem
            if hasattr(adapter, "adapt_setitem"):
                name, value = adapter.adapt_setitem(context, name, value)

        return name, value
