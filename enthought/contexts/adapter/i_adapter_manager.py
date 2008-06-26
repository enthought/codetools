from enthought.traits.api import Interface

class IAdapterManager(Interface):
    """ Handles management of an adapter stack for objects that implement
    IContext.
    """

    def push_adapter(self, adapter):
        """ Add an adapter to the 'top' of the adapter stack.
        """

    def pop_adapter(self):
        """ Remove the 'top' from the top of the adapter stack.

            fixme: How to handle if the stack is empty?
        """
