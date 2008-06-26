# Enthought library imports
from enthought.traits.api import Instance, List

# Geo library imports
from i_context import IContext
from adapter.i_adapter import IAdapter


class IAdaptedDataContext(IContext):
    """ A context with adapters.
    """

    # List of adapters that are used to modify data as it is saved/retreived
    # from the underlying context.
    adapters = List(Instance(IAdapter))


    def push_adapter(self, adapter):
        """ Add an adapter to the 'top' of the adapter stack.
        """

    def pop_adapter(self):
        """ Remove the 'top' from the top of the adapter stack.
        """


