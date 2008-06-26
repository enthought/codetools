# Enthought library imports
from enthought.traits.api import implements

# Local imports
from i_adapted_data_context import IAdaptedDataContext
from adapter.adapter_manager_mixin import AdapterManagerMixin
from data_context import DataContext


class AdaptedDataContext(DataContext, AdapterManagerMixin):
    """ A Context (namespace) for holding multiple geophysical objects.

    Users can store related logs and data within a GeoContext.  It can be used
    as an execution namespace for expressions or adapted in a number of ways to
    provide operations on a masked set of its data, unit conversion of the data,
    enforcement that values retreived from the namespace (even if they are
    scalars) are retreived as arrays of a certain size, etc.
    """

    implements(IAdaptedDataContext)

    ### Type compatibility #####################################################

    def allows(self, value, name=None):
        """ Determine whether value is allowed in this context.

            fixme: Adapters are not used in this calculation yet.  They
            should be.
        """

        return self.subcontext.allows(value, name)


    ############################################################################
    # object interface
    ############################################################################

    # Pass any unknown attributes to self.subcontext
    def __getattr__(self, attr):
        return getattr(self.subcontext, attr)


    ############################################################################
    # Dictionary-like interface
    ############################################################################

    def keys(self):
        """ Return the list of variables available in context.
        """
        return self.subcontext.keys()

    def __delitem__(self, name):
        """ Delete an item out of the context.
        """

        name = self._adapt_name(self.subcontext, name)
        del self.subcontext[name]


    def __getitem__(self, name):
        """ Get the value bound to the variable 'name' from the context.
        """
        name = self._adapt_name(self.subcontext, name)
        value = self.subcontext[name]
        # fixme: We really need to think about whether context is part
        #        of this api, and if so, which context to pass in.
        name, value = self._adapt_getitem(self.subcontext, name, value)

        return value

    def __setitem__(self, name, value):
        """ Set the variable 'name' = value in the context.
        """

        # fixme: We really need to think about whether context is part
        #        of this api, and if so, which context to pass in.
        name = self._adapt_name(self.subcontext, name)
        name, value = self._adapt_setitem(self.subcontext, name, value)
        self.subcontext[name] = value
