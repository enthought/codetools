""" Context holding multiple subcontexts.
"""

from itertools import chain
from UserDict import DictMixin

from enthought.traits.api import (Instance, List, Str, Undefined, implements,
    on_trait_change)
from enthought.traits.protocols.api import adapt

from data_context import DataContext, ListenableMixin, PersistableMixin
from i_context import (ICheckpointable, IListenableContext,
    IPersistableContext, IRestrictedContext)
from utils import safe_repr



class MultiContext(ListenableMixin, PersistableMixin, DictMixin):
    """ Wrap several subcontexts.
    """

    implements(ICheckpointable, IListenableContext, IPersistableContext, IRestrictedContext)

    # The name of the context.
    name = Str("multidummy")

    # The underlying dictionary.
    subcontexts = List(Instance(IRestrictedContext, factory=DataContext,
        adapt='yes'))


    def __init__(self, *subcontexts, **traits):
        subcontexts = list(subcontexts)
        super(MultiContext, self).__init__(subcontexts=subcontexts, **traits)


    #### IContext interface ####################################################

    def __contains__(self, key):
        for c in self.subcontexts:
            if key in c:
                return True
        return False

    def __delitem__(self, key):
        """ Remove the given key with [] access.

        Only deletes the first instance of the key.

        Parameters
        ----------
        key : str

        Raises
        ------
        KeyError if the kew is not available in the context.
        """
        for c in self.subcontexts:
            try:
                del c[key]
                return
            except KeyError:
                continue
        raise KeyError(key)

    def __getitem__(self, key):
        for c in self.subcontexts:
            try:
                return c[key]
            except KeyError:
                continue
        raise KeyError(key)

    def __setitem__(self, key, value):
        """ Set item with [] access.

        The first subcontext which allows the key/value pair will get it. If an
        earlier subcontext has the key, but does not allow the assignment, then
        that key will be deleted. Later contexts with the key will be untouched.
        
        If the key/value pair cannot be assigned to anything, no deletion will
        take place.

        Parameters
        ----------
        key : str
        value : object

        Raises
        ------
        ValueError if the key is not permitted to be assigned that value.
        """

        # Let subtypes dictate compatibility independently of contained contexts
        if not self.allows(value, key):
            raise ValueError('Disallowed mapping: %s = %s' % (key, safe_repr(value)))

        set = False
        blocking_contexts = []
        for c in self.subcontexts:
            if not set:
                if c.allows(value, key):
                    if key in c:
                        added = []
                        modified = [key]
                    else:
                        added = [key]
                        modified = []
                    c[key] = value
                    set = True
                    break
                elif key in c:
                    # Record this context as blocking access to the final
                    # location of the value.
                    blocking_contexts.append(c)

        # Remove all blocking instances.
        for c in blocking_contexts:
            del c[key]

        if not set:
            raise ValueError('Disallowed mapping: %s = %s' % (key, safe_repr(value)))

    def keys(self):
        return list(set(chain(*[c.keys() for c in self.subcontexts])))


    # Expose DictMixin's get method over HasTraits'.
    get = DictMixin.get

    def __str__(self):
        # Maybe a good default string
        subcontext_str = '[%s]' % ', '.join([str(x) for x in self.subcontexts])
        return '%s(name=%r, subcontexts=%s)' % (type(self).__name__, self.name,
            subcontext_str)

    def __repr__(self):
        # Maybe a good default representation
        return '%s(name=%r)' % (type(self).__name__, self.name)


    #### IRestrictedContext interface ##########################################

    def allows(self, value, name=None):
        for c in self.subcontexts:
            if c.allows(value, name=name):
                return True
        return False


    #### Trait Event Handlers ##################################################

    @on_trait_change('subcontexts:items_modified')
    def subcontexts_items_modified(self, event):
        """ Pass events up.
        """
        if event is Undefined:
            # Nothing to do.
            return

        event.veto = True

        self._fire_event(added=event.added, removed=event.removed,
            modified=event.modified, context=event.context)
    
    def _subcontexts_items_changed(self, event):
        """ Trait listener for items of subcontexts list.
        """
        added = []
        removed = []

        # Add to the list of items added
        if len(event.added):
            for context in event.added:
                added.extend(context.keys())

        # Add to the list of items removed
        if len(event.removed):
            for context in event.removed:
                removed.extend(context.keys())

        self._fire_event(added=added, removed=removed)

    #### ICheckpointable interface ############################################

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
        copy = self.clone_traits()
        new_subcontexts = []
        for context in self.subcontexts:
            checkpointable_subcontext = adapt(context, ICheckpointable)
            new_subcontexts.append(checkpointable_subcontext.checkpoint())
        copy.subcontexts = new_subcontexts
        return copy

