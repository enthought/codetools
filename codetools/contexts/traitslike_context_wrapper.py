#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#

""" A wrapper around IListenableContexts which expose a standard HasTraits
interface to its contents.
"""

from __future__ import absolute_import

from contextlib import contextmanager

from traits.api import (Any, Bool, HasTraits, Supports, Trait,
    Undefined, on_trait_change)

from .i_context import IListenableContext


class TraitslikeContextWrapper(HasTraits):
    """ Wrap a context with traits, primarily for use with Traits UI.
    """

    # These traits are _private so as to avoid name conflicts with the traits
    # that mirror the context.

    # The context we are wrapping.
    _context = Supports(IListenableContext, rich_compare=False)

    # Whether the communication between traits and context is currently active
    # or not.
    _synched = Bool(True)

    def add_traits(self, *args, **kwds):
        """ Add a set of traits to this object.

        Each trait corresponds to a name in the context. Each CTrait which is
        added will have .in_context metadata attribute as True.

        Parameters
        ----------
        ``*args`` : strs
            These attributes will be created as Any traits.
        ``**kwds`` : str -> Trait
            These attributes will be created as the specified Traits.

        Example
        -------
        >>> from traits.api import Int
        >>> from codetools.contexts.traitslike_context_wrapper import TraitsLikeContextWrapper
        >>> tcw = TraitsLikeContextWrapper(_context={})
        >>> tcw.add_traits('a', 'b', c=Int)
        """
        if self._context is not None:
            keys = self._context.keys()
        else:
            keys = []

        with self._synch_off():
            for name, trait in [(x, Any()) for x in args] + kwds.items():
                self.add_trait(name, Trait(trait, in_context=True))
                # Set the value to that in the context.
                if name in keys:
                    setattr(self, name, self._context[name])
                else:
                    # ... or vice-versa.
                    self._context[name] = getattr(self, name)

    def _in_context_traits(self):
        """ Return a list of names of all of the traits which mirror context
        variables.
        """
        in_context_traits = []
        for name in self.trait_names():
            ctrait = self.trait(name)
            if ctrait.in_context:
                in_context_traits.append(name)
        return in_context_traits

    @on_trait_change('_context')
    def _context_changed(self, object, name, old, new):
        if old is not None:
            old.on_trait_change(self._context_items_modified, 'items_modified', remove=True)
        if new is not None:
            new.on_trait_change(self._context_items_modified, 'items_modified')

    #@on_trait_change('_context.items_modified')
    def _context_items_modified(self, event):
        """ Receive change notifications from the context.
        """
        if not self._synched or event is Undefined:
            # Nothing to do.
            return
        with self._synch_off():
            in_context_traits = self._in_context_traits()
            for name in event.added + event.modified:
                if name in in_context_traits:
                    setattr(self, name, self._context[name])

    # The decorator doesn't work. See #1327
    #@on_trait_change('+in_context')
    def _in_context_trait_changed(self, name, new):
        """ Generic trait change handler to propogate mirrored trait changes
        into the context.
        """
        if not self._synched:
            # Nothing to do.
            return

        with self._context.deferred_events():
            # Set the trait with synching off, then turn synching on before
            # firing events
            with self._synch_off():
                self._context[name] = new

    # Instead, do this.
    def _anytrait_changed(self, name, old, new):
        trait = self.trait(name)
        if trait.in_context:
            self._in_context_trait_changed(name, new)

    @contextmanager
    def _synch_off(self):
        # XXX not thread-safe
        _old_synched = self._synched
        self._synched = False
        try:
            yield
        finally:
            self._synched = _old_synched
            

