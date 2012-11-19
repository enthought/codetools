import threading
import time
from concurrent.futures import Future, Executor
from concurrent.futures import ThreadPoolExecutor

from codetools.contexts.data_context import DataContext
from codetools.execution.executing_context import ExecutingContext
from codetools.execution.interfaces import IListenableContext
from codetools.execution.restricting_code_executable import (
        RestrictingCodeExecutable)
from traits.api import (Instance, Dict, Event, Code, Any, Long,
        on_trait_change, Bool, Undefined)


class AsyncExecutingContext(ExecutingContext):
    """Sequential, threaded pipeline for execution of a Block.

    This uses a (possibly shared) Executor to asyncronously execute a block
    within a context. This will only consume a single worker at a time from the
    Executor. Changes to the context are made with the '__setitem__' method
    (dictionary update) and may trigger an execution of the block, with inputs
    restricted to the current, cumulative set of context changes.  Updates made
    while the block is being executed will result in an accumulation of the
    changes and execution of the block once the current execution completes.

    """

    # The code string
    code = Code

    # The codeblock that contains the pipeline code
    executable = Any

    # The local execution namespace
    subcontext = Instance(IListenableContext, factory=DataContext, adapt='yes',
        rich_compare=False)

    # Fired when an exception occurs during execution.
    # Carries the exception.
    exception = Event

    # An Executor with which to dispatch work.
    executor = Instance(Executor)

    # The future object used for concurrent execution
    _future = Instance(Future)

    # The cumulative changes in the context since the last successful execution
    _context_delta = Dict

    # Counters used for the _wait() method
    _pending_update = Long(0)
    _completed_update = Long(0)

    # Flag used to suppress events when internally modifying subcontext
    _suppress_events = Bool(False)

    # A lock for shared data
    _data_lock = Instance(threading.Lock, ())

    # A lock future access
    _future_lock = Instance(threading.Lock, ())

    def execute_for_names(self, names=None):
        """ Possibly execute for a set of names which have been changed.

        Parameters
        ----------
        names : list of str, optional
            If not provided, then we'll just re-execute the whole thing.
        """

        if names is None or None in names:
            # A total re-execution has been requested.
            self.execute()
        else:
            affected_names = list(set(names))
            context = {}
            with self._data_lock:
                for key in affected_names:
                    context[key] = self.subcontext[key]
            self._wait()
            with self._data_lock:
                self._pending_update += 1
                self._context_delta.update(context)
            self._update()

    def execute(self):
        """Update the context by executing the full block.
        This executes asyncronously.

        """
        # Fill in _context_delta with _context. We're telling _update that
        # everything changed.
        with self._data_lock:
            for key, value in self.subcontext.iteritems():
                if key not in self._context_delta:
                    self._context_delta[key] = value
            self._pending_update += 1

        # Trigger update
        self._update()

    def __setitem__(self, name, value):
        """Assign a new value into the namespace.

        This triggers an asyncronous update of the context via execution of the
        block.  The 'updated' event will be fired when the execution completes.

        Parameters
        ----------
        name : str
            The name of the variable to assign
        value : any
            The value to be assigned

        """

        # Update _context_delta
        with self._data_lock:
            self._context_delta[name] = value
            self._pending_update += 1
            context = dict(self.subcontext)
            if name in context:
                added = []
                modified = [name]
            else:
                modified = []
                added = [name]
            context.update(self._context_delta)

        self._update()

        #Fire event with what changed
        self._fire_event(added=added, modified=modified, context=context)

    def __delitem__(self, name):
        del self.subcontext[name]

    def _update(self):
        """Update based on changes in _context_delta"""

        # If there is no delta, we have no work to do
        if not self._context_delta:
            return

        # If we are defering we should simply accumulate deltas and not execute
        if self.defer_execution:
            return

        with self._future_lock:
            # If we already have a future, then we get out of here.
            if self._future is not None:
                return

            # Create a new future
            self._future = self.executor.submit(self._update_worker)

            # Add a callback to update listeners
            self._future.add_done_callback(self._update_callback)

    def _update_worker(self):
        """Worker for the _update method.

        Returns
        -------
        updated_vars : set
            The names of updated variables. This includes input and output
            variables.
        context : dict
            The updated context
        update_id : Long
            The id of the current update call


        """

        # Get the current context, apply then delete the delta
        with self._data_lock:
            updated_vars = set(self._context_delta.keys())
            update_id = self._pending_update
            self._suppress_events = True
            self.subcontext.update(self._context_delta)
            self._suppress_events = False
            context_delta = self._context_delta.copy()
            self._context_delta.clear()

        if not updated_vars:
            return updated_vars, self.subcontext, update_id

        try:
            self.subcontext.defer_events = True
            inputs, outputs = self.executable.execute(self.subcontext,
                    inputs=updated_vars)
            self.subcontext.defer_events = False
        except Exception:
            with self._data_lock:
                context_delta.update(self._context_delta)
                self._context_delta = context_delta
            raise

        # Report on what was changed
        return updated_vars, self.subcontext, update_id

    def _update_callback(self, future):
        """Callback for the _update_worker future"""

        # Check for and report exceptions
        exception = future.exception()
        if exception is not None:
            self.exception = exception
            self._completed_update = -1  # We are currently in an error state
            return

        # Get the result
        updated_vars, context, update_id = future.result()
        self._completed_update = update_id
        self._future = None

        # Try to call _update again
        self._update()

    ###########################################################################
    #### Trait defaults
    ###########################################################################

    def _executor_default(self):
        return ThreadPoolExecutor(2)

    def _executable_default(self):
        return RestrictingCodeExecutable(code=self.code)

    ###########################################################################
    #### Trait change handlers
    ###########################################################################

    def _code_changed(self, old, new):
        try:
            self.executable.code = new
        except Exception, e:
            self.exception = e
            self.code = old
            return
        self.execute()

    def _defer_execution_changed(self, old, new):
        self._update()

    @on_trait_change('subcontext.items_modified')
    def subcontext_items_modified(self, event):
        if event is Undefined:
            # Nothing to do.
            return

        if self._suppress_events:
            # These events were already manually fired in __setitem__()
            return

        event.veto = True
        self._fire_event(added=event.added, removed=event.removed,
            modified=event.modified, context=event.context)

    ###########################################################################
    #### Private Methods
    ###########################################################################

    def _wait(self):
        """ Wait atleast until all previous assignments are finished, possibly
        longer

        """
        pending = self._pending_update

        while pending > self._completed_update:
            #This can happen if there is an exception
            if self._completed_update == -1:
                return
            time.sleep(.001)


if __name__ == '__main__':
    executor = ThreadPoolExecutor(2)
    ns = dict(a=3, b=4.5)
    code = "c = a + b"

    wait_time = 0.2

    pipeline = AsyncExecutingContext(context=ns, code=code, executor=executor)

    def printer(args):
        print 'notification:', args

    print "initial assignment"
    event = threading.Event()
    pipeline.on_trait_change(event.set, 'updated')
    pipeline.on_trait_change(printer, 'updated')
    pipeline.on_trait_change(printer, 'exception')
    event.wait(wait_time)
    print pipeline.context

    print "assign c"
    event.clear()
    pipeline['c'] = 4
    event.wait(wait_time)
    print pipeline.context

    print "assign a"
    event.clear()
    pipeline['a'] = 4
    event.wait(wait_time)
    print pipeline.context

    print "update code"
    event.clear()
    pipeline.code = 'c = a**2 + b; d = c - a'
    event.wait(wait_time)
    print pipeline.context

    print "rapid update"
    updates = 0
    for i in xrange(10):
        event.clear()
        pipeline['a'] = i
    event.wait(wait_time)
    print pipeline.context

    print "code error"
    event.clear()
    pipeline.code = 'c = a**2 + b; d = c - z'
    event.wait(wait_time)
    event.clear()
    pipeline.code = 'c = a^2 + in'
    event.wait(wait_time)
