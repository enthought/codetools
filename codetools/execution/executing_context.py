#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
""" Define an IContext which will execute code in response to changes in its
namespace.
"""
from __future__ import absolute_import

from traits.api import (Bool, HasTraits, List, Str, Supports,
    Undefined, adapt, provides, on_trait_change)

from codetools.contexts.data_context import DataContext
from codetools.contexts.i_context import IContext, IListenableContext
from .interfaces import IExecutable, IExecutingContext


@provides(IExecutable)
class CodeExecutable(HasTraits):
    """ Simple IExecutable that plainly executes a piece of code.
    """

    # The code to execute.
    code = Str("pass")

    def execute(self, context, globals=None, inputs=None, outputs=None):
        icontext = adapt(context, IContext)

        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        if globals is None:
            globals = {}

        exec self.code in globals, icontext
        return set(inputs), set(outputs)


@provides(IExecutingContext)
class ExecutingContext(DataContext):
    """ A context which will execute code in response to changes in its
    namespace.
    """

    # Override to provide a more specific requirement.
    subcontext = Supports(IListenableContext, factory=DataContext,
        rich_compare=False)

    executable = Supports(IExecutable, factory=CodeExecutable)

    defer_execution = Bool(False)

    # When execution is deferred, we need to keep a list of these events.
    _deferred_execution_names = List(Str, transient=True)

    def execute_for_names(self, names):
        """ Possibly execute for a set of names which have been changed.

        Parameters
        ----------
        names : list of str, optional
            If not provided, then we'll just re-execute the whole thing.
        """
        if self.defer_execution:
            if names is None:
                names = [None]
            self._deferred_execution_names.extend(names)
            return

        if names is None or None in names:
            # A total re-execution has been requested.
            affected_names = None
        else:
            affected_names = list(set(names))
        with self.subcontext.deferred_events():
            self.executable.execute(self.subcontext, inputs=affected_names)

    #### IContext interface ####################################################

    def __setitem__(self, key, value):
        self.subcontext[key] = value
        self.execute_for_names([key])

    def __delitem__(self, key):
        del self.subcontext[key]
        self.execute_for_names([key])

    #### Trait Event Handlers ##################################################

    @on_trait_change('defer_execution')
    def _defer_execution_changed(self, old, new):
        self._defer_execution_changed_refire(new)

    def _defer_execution_changed_refire(self, new):
        if not new:
            self.execute_for_names(self._deferred_execution_names)

            # Reset the deferred names.
            self._deferred_execution_names = []

    @on_trait_change('subcontext.items_modified')
    def subcontext_items_modified(self, event):
        if event is Undefined:
            # Nothing to do.
            return

        event.veto = True

        self._fire_event(added=event.added, removed=event.removed,
            modified=event.modified, context=event.context)
