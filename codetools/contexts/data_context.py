#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#

""" Basic implementation of the IListenableContext, IPersistableContext, and
IRestrictedContext interfaces.
"""

from __future__ import absolute_import

from collections import MutableMapping as DictMixin
from contextlib import contextmanager
import pickle

from apptools.persistence.versioned_unpickler import VersionedUnpickler
from traits.adaptation.api import (
    AdaptationOffer, get_global_adaptation_manager)
from traits.api import (
    ABCHasTraits, Bool, Dict, HasTraits, Str, Supports, adapt, on_trait_change,
    provides)

from .i_context import IContext, ICheckpointable, IDataContext
from .items_modified_event import ItemsModifiedEvent, ItemsModified

# This is copied from numerical_modeling.numeric_context.constants
from numpy import ufunc
from types import FunctionType, MethodType, ModuleType
NonPickleable = [FunctionType, MethodType, ModuleType, ufunc]

def cannot_pickle(type):
    global NonPickleable
    if type not in NonPickleable:
        NonPickleable.append(type)


class ListenableMixin(ABCHasTraits):
    """ Mixin to provide much of the standard IListenableContext implementation.
    """

    # Fired when something changes in the context.
    items_modified = ItemsModifiedEvent

    # Whether to buffer 'items_modified' events. When true, no events are fired,
    # and when reverted to false, one single event fires that represents the net
    # change since 'defer_events' was set.
    defer_events = Bool(False)
    _deferred_events = Dict(transient=True)

    @contextmanager
    def deferred_events(self):
        """ Context manager that sets defer_events to False """
        # XXX not thread safe!
        _old_defer_events = self.defer_events
        self.defer_events = False
        try:
            yield
        finally:
            self.defer_events = _old_defer_events

    #### Trait Event Handlers ##################################################

    @on_trait_change('defer_events')
    def _defer_events_changed(self, old, new):
        return self._defer_events_changed_refire(new, 'items_modified')

    def _defer_events_changed_refire(self, new, event_attribute='items_modified'):
        if not new:
            for key, event in list(self._deferred_events.items()):

                added = event.added
                removed = event.removed
                modified = event.modified

                if (len(added) + len(removed) + len(modified)) > 0:
                    new_event = ItemsModified(
                        context=event.context,
                        added=added,
                        removed=removed,
                        modified=modified,
                    )
                    setattr(self, event_attribute, new_event)

                # Reset the deferred event.
                # Just in case triggering the event changed things, we'll guard
                # this delete.
                self._deferred_events.pop(key, None)


    #### Private API ###########################################################

    def _fire_event(self, added=None, removed=None, modified=None,
        event_attribute='items_modified', context=None):
        """ Fire an ItemsModifiedEvent.

        Parameters
        ----------
        added : list of str, optional
        removed : list of str, optional
        modified : list of str, optional
            The names of items that have been added to, removed from, or
            modified in the context.
        event_attribute : str, optional
            The name of the event on this object.
        context : IContext, optional
            The context in which these changes actually occured. If not
            provided, then self will be used.
        """
        if added is None:
            added = []
        if removed is None:
            removed = []
        if modified is None:
            modified = []
        if context is None:
            context = self
        if len(added) + len(removed) + len(modified) > 0:
            if self.defer_events:
                # keep the context the same as the context that fired this event to
                # ensure the right context gets re-executed
                self._add_deferred_event(context, added, removed, modified)
            else:
                new_event = ItemsModified(
                    context=context,
                    added=added,
                    removed=removed,
                    modified=modified,
                )
                setattr(self, event_attribute, new_event)

    def _add_deferred_event(self, context, added, removed, modified):
        """ Defer this event.

        Parameters
        ----------
        context : IContext
        added : list of str
        removed : list of str
        modified : list of str
        """
        if id(context) not in self._deferred_events:
            self._deferred_events[id(context)] = ItemsModified(context=context)

        event = self._deferred_events[id(context)]

        event.added = list(set(event.added) | set(added))
        for key in removed:
            if key in event.added:
                # If we've already deferred the addition of this key, then
                # removing the key should cancel the addition.
                event.added.remove(key)
            else:
                event.removed.append(key)
                # Don't record prior modifications.
                if key in event.modified:
                    event.modified.remove(key)
        event.removed = list(set(event.removed))
        for key in modified:
            if key not in event.added:
                event.modified.append(key)
        event.modified = list(set(event.modified))



class PersistableMixin(ABCHasTraits):
    """ Provide the persistence method implementations for contexts.
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

        if hasattr(file_or_path, 'read'):
            # Already a readable file object.
            should_close = False
            file_object = file_or_path
        else:
            # Open the file.
            should_close = True
            file_object = open(file_or_path, 'rb')

        try:
            data_context = VersionedUnpickler(file_object).load()
        finally:
            if should_close:
                file_object.close()

        return data_context

    def save(self, file_or_path):
        """ Pickle the data context out to a file

        Parameters
        ----------
        file_or_path : str or writable filelike object
        """

        # Check if there is a key called 'context' that references to its
        # bindings
        if 'context' in self and self['context'] == self._bindings:
            self.pop('context')

        if hasattr(file_or_path, 'write'):
            # File is already opened. Will not close.
            should_close = False
            file_object = file_or_path
        else:
            should_close = True
            file_object = open(file_or_path, 'wb')

        try:
            # Filter out nonpickleable data from the context dictionary
            for item in self.keys():
                if isinstance(self[item], tuple(NonPickleable)):
                    del self[item]
            pickle.dump(self, file_object, 1)
        finally:
            if should_close:
                file_object.close()


@provides(IDataContext)
class DataContext(ListenableMixin, PersistableMixin, DictMixin):
    """ A simple context which fires events.
    """

    # The name of the context.
    name = Str()

    # The underlying dictionary.
    subcontext = Supports(IContext, factory=dict)


    #### IContext interface ####################################################

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.subcontext)

    def __contains__(self, key):
        return key in self.subcontext

    def __getitem__(self, key):
        return self.subcontext[key]

    def __setitem__(self, key, value):
        if not self.allows(value, key):
            raise ValueError("cannot assign value: %s = %s" % (key, value))
        # Figure out if the item was added or modified
        added = []
        modified = []
        if key in self.subcontext:
            modified = [key]
        else:
            added = [key]

        self.subcontext[key] = value

        # Event fired so that GUI listeners can update
        self._fire_event(added=added, modified=modified)

    def __delitem__(self, key):
        if key in self.subcontext:
            del self.subcontext[key]
            self._fire_event(removed=[key])
        else:
            raise KeyError(key)

    def keys(self):
        """ Returns the list of keys available in the context.

        Returns
        -------
        keys : list of str
        """
        return list(self.subcontext.keys())

    # Expose DictMixin's get method over HasTraits'.
    get = DictMixin.get

    def __str__(self):
        # Maybe a good default string
        return '%s(name=%r)' % (type(self).__name__, self.name)

    def __repr__(self):
        # Maybe a good default representation
        return '%s(name=%r)' % (type(self).__name__, self.name)

    #### DictMixin interface ##################################################

    def __eq__(self, other):
        """ Don't allow objects of different classes to be equal.

        This will allow different instances with different names but the same
        keys and values to be equal. Subclasses may wish to override this to
        compare different attributes.
        """
        if type(other) is not type(self):
            return False
        return DictMixin.__eq__(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    #### IRestrictedContext interface ##########################################

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
        # WORKAROUND: subclassing from DataContext can cause the adapter to put the real
        # context in subcontext if used in a class which adapts. In this case
        # call allows on the real context. This only happens occasionally and is a bug.
        if self.subcontext is not None and isinstance(self.subcontext, DataContext):
            return self.subcontext.allows(value, name)
        return True

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
        checkpointable_subcontext = adapt(self.subcontext, ICheckpointable)
        copy.subcontext = checkpointable_subcontext.checkpoint()
        return copy


# Define adaptation offers from IContext to other context protocols using
# DataContext.

data_context_offer = AdaptationOffer(
    factory=lambda x: DataContext(subcontext=x),
    from_protocol=IContext,
    to_protocol=IDataContext
)


def register_i_context_adapter_offers(adaptation_manager):
    """ Register adapters from the `dict` object to `codetools` protocols.

    1) `dict` provides the `IContext` interface
    2) `dict` can be adapted to `ICheckpointable`
    """

    adaptation_manager.register_offer(data_context_offer)


# For backward compatibility, we register the adapters from `dict` globally
# at import time.
register_i_context_adapter_offers(get_global_adaptation_manager())
