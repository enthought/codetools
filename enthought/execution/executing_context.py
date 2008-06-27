""" Define an IContext which will execute code in response to changes in its
namespace.
"""

from enthought.traits.api import (Bool, HasTraits, Instance, List, Str,
    Undefined, implements, on_trait_change)
from enthought.traits.protocols.api import adapt

from enthought.block_canvas.context.data_context import DataContext
from enthought.block_canvas.context.i_context import IContext, IListenableContext
from interfaces import IExecutable, IExecutingContext



class CodeExecutable(HasTraits):
    """ Simple IExecutable that plainly executes a piece of code.
    """

    implements(IExecutable)

    # The code to execute.
    code = Str("pass")

    def execute(self, context, globals=None, inputs=None, outputs=None):
        icontext = adapt(context, IContext)

        if globals is None:
            globals = {}

        exec self.code in globals, icontext



class ExecutingContext(DataContext):
    """ A context which will execute code in response to changes in its
    namespace.
    """

    implements(IExecutingContext)

    # Override to provide a more specific requirement.
    subcontext = Instance(IListenableContext, factory=DataContext, adapt='yes',
        rich_compare=False)

    executable = Instance(IExecutable, factory=CodeExecutable, adapt='yes')

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
        self.subcontext.defer_events = True
        self.executable.execute(self.subcontext, inputs=affected_names)
        self.subcontext.defer_events = False


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


