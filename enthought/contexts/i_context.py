from enthought.traits.api import Bool, Interface, Str
from enthought.traits.protocols.api import declareAdapter, declareImplementation

from items_modified_event import ItemsModifiedEvent


class IContext(Interface):
    """ A context which can be used for executing code in.

    The __*item__ methods are the minimal methods necessary for execution. They,
    plus keys(), form the minimal set of methods that need to be implemented for
    UserDict.DictMixin to provide the rest of the dictionary interface.

    __contains__ is added to the interface because it is too useful to omit.

    Note that __setitem__ can raise a ValueError.
    """

    def __contains__(self, key):
        """ Test whether the key is available in the context or not.

        Parameters
        ----------
        key : str

        Returns
        -------
        contains : bool
        """

    def __getitem__(self, key):
        """ Get item with [] access.

        Parameters
        ----------
        key : str

        Returns
        -------
        obj : object

        Raises
        ------
        KeyError if the key is not available in the context.
        """

    def __setitem__(self, key, value):
        """ Set item with [] access.

        Parameters
        ----------
        key : str
        value : object

        Raises
        ------
        ValueError if the key is not permitted to be assigned that value.
        """

    def __delitem__(self, key):
        """ Remove the given key with [] access.

        Parameters
        ----------
        key : str

        Raises
        ------
        KeyError if the kew is not available in the context.
        """

    def keys(self):
        """ Returns the list of keys available in the context.

        Returns
        -------
        keys : list of str
        """

    # XXX: The dotted forms for handling sub-contexts?

# Python dictionaries satisfy the interface.
declareImplementation(dict, [IContext])


class IListenableContext(IContext):
    """ A context that fires events when it is modified.
    """

    # The name of the context.
    name = Str("")

    # Fired when something changes in the context.
    items_modified = ItemsModifiedEvent

    # Whether to buffer 'items_modified' events. When true, no events are fired,
    # and when reverted to false, one single event fires that represents the net
    # change since 'defer_events' was set.
    defer_events = Bool(False)


class IRestrictedContext(IContext):
    """ A context that has certain restrictions on the values it is allowed to
    contain.
    """

    def allows(self, value, name=None):
        """ Determines whether this value is allowed in this context. Only
        strings are allowed for 'name'.

        Typically, this is used to limit the types of objects allowed into the
        context.  It could also be used to restrict specific values (ie. the
        shape of an array) and even on the name...

        Parameters
        ----------
        value : object
        name : str, optional

        Returns
        -------
        allowed : bool
        """


class IPersistableContext(IContext):
    """ Add loading and saving to the interface.
    """

    @staticmethod
    def load(file_or_path):
        """ Unpickle the context from a file

        Parameters
        ----------
        file_or_path : str or readable filelike object

        Returns
        -------
        context : object
        """

    def save(self, file_or_path):
        """ Pickle the data context out to a file

        Parameters
        ----------
        file_or_path : str or writable filelike object
        """


class ICheckpointable(Interface):
    """ A context which can be copied.
    """

    def checkpoint(self):
        """ Make a shallow copy of the context.

        Technically, this is actually a fairly deep copy. All of the object
        structure should be replicated, but the actual dictionary storage will
        be shallowly copied::

            copy = context.shallow_copy()
            copy[key] is context[key] for key in context.keys()

        These semantics are useful for saving out checkpointed versions of the
        context for implementing an undo/redo stack. They may not be useful for
        other purposes.

        Returns
        -------
        copy : IContext
        """
        # For implementors: DataContext and MultiContext provide generally
        # useful implementations of this method. If you subclass from these and
        # you don't store complicated state besides the subcontext(s), you
        # probably don't need to override this.
        #
        # If you keep other state in List or Dict traits, then the
        # HasTraits.clone() semantics force a shallow copy of these traits. If
        # you store mutable objects like lists and dicts using Any traits, then
        # HasTraits.clone() will pass along the reference instead of making
        # a shallow copy. Modifications to that trait in the original will
        # propagate to the copy. This is not desirable.
        #
        # However, if the trait is declared with copy='shallow' metadata, then
        # HasTraits.clone_traits() will do the right thing. This is preferred.
        #
        # Subcontexts of either DataContext or MultiContext should be adaptable
        # to the ICheckpointable interface. An adapter for dicts is provided
        # here.


class CheckPointableDictAdapter(object):
    """ Adapt a dictionary to the ICheckpointable interface.
    """
    def __init__(self, dict):
        self.dict = dict

    def checkpoint(self):
        return self.dict.copy()

declareAdapter(
    CheckPointableDictAdapter,
    [ICheckpointable],
    forTypes=[dict],
)


