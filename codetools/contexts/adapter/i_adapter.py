from traits.api import ABCHasTraits


class IAdapter(ABCHasTraits):
    """ Handles management of an adapter stack for objects that implement
        IContext.
    """

    ############################################################################
    # IAdapterManager public interface
    ############################################################################

    def adapt_name(self, context, name):
        """ Apply the adapter to names sent to a context through __setitem__
            and __getitem__.

            Returns a name.

            Note: This method is optional.
        """
        raise NotImplementedError

    def adapt_keys(self, context, name):
        """ Returns an iterable containing any keys (names) defined by this
            adapter. Should return all names which could successfully be passed
            to adapt_name.

            Note: This method is optional, useful only if adapt_name is
            implemented.
        """
        raise NotImplementedError

    def adapt_getitem(self, context, name, value):
        """ Apply the adapter to values accessed through __getitem__ of a
            context.

            context: The context being adapted.
            name: Name of variable sent to Context.__setitem__
            value: Value of variable sent to Context.__setitem__

            Returns a name/value pair.
        """
        return NotImplementedError

    def adapt_setitem(self, context, name, value):
        """ Apply the adapter to values sent to a context through __setitem__.

            context: The context being adapted.
            name: Name of variable sent to Context.__setitem__
            value: Value of variable sent to Context.__setitem__

            Returns a name/value pair.
        """
        return NotImplementedError
