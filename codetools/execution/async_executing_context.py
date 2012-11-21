import threading
import time
from concurrent.futures import Executor
from concurrent.futures import ThreadPoolExecutor

from codetools.contexts.data_context import DataContext
from codetools.execution.executing_context import ExecutingContext
from codetools.execution.interfaces import IListenableContext
from codetools.execution.restricting_code_executable import (
        RestrictingCodeExecutable)
from traits.api import (Instance, Dict, Event, Code, Any, on_trait_change, Bool,
        Undefined, Enum)


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

    # The cumulative changes in the context since the last successful execution
    _context_delta = Dict

    # Flag used to suppress events when internally modifying subcontext
    _suppress_events = Bool(False)

    # A lock for shared data
    _data_lock = Instance(threading.Lock, ())

    ###########################################################################
    #### AsyncExecutingContext Interface
    ###########################################################################

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

        self._update()

    ###########################################################################
    #### ExecutingContext Interface
    ###########################################################################

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
            # Copy the affected names into the delta to signal that the block
            # should be executed as though they changed
            affected_names = list(set(names))
            context = {}
            with self._data_lock:
                for key in affected_names:
                    context[key] = self.subcontext[key]

            self._wait()  # wait until the delta is empty

            with self._data_lock:
                self._context_delta.update(context)

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

        with self._data_lock:
            self._context_delta[name] = value
            context_copy = dict(self.subcontext)
            if name in context_copy:
                added = []
                modified = [name]
            else:
                modified = []
                added = [name]
            context_copy.update(self._context_delta)
        self._fire_event(added=added, modified=modified, context=context_copy)

        self._update()

    def __delitem__(self, name):
        del self.subcontext[name]

    ###########################################################################
    #### Concurrency methods and state machine.
    ###########################################################################

    # A lock for state changes
    _state_lock = Instance(threading.Condition, ())

    # Flag indicating whether we're currently 'deferred' or not.  True
    # iff execution is deferred.
    _on_hold = Bool(False)

    # Flag indicating whether there's a currently scheduled task or not.
    # True iff there's no currently scheduled or executing future, else
    # True.
    _idle = Bool(True)

    # Flag indicating whether there's a need to do a new update at
    # some point.
    _pending = Bool(False)

    def _dispatch_task(self):
        """Start executing a pending task if appropriate.

        Return either the future or None if no task started.

        """
        if self._idle and self._pending and not self._on_hold:
            self._idle = self._pending = False
            return self.executor.submit(self._worker)
        else:
            return None

    def _update(self):
        """Update based on changes in _context_delta."""
        with self._state_lock:
            self._pending = True
            future = self._dispatch_task()
            self._state_lock.notify_all()

        if future is not None:
            future.add_done_callback(self._callback)

    def _callback(self, future):
        """Callback for the _worker"""
        with self._state_lock:
            self._idle = True
            future = self._dispatch_task()
            self._state_lock.notify_all()

        if future is not None:
            future.add_done_callback(self._callback)

    def _resume(self):
        """Resume execution."""
        with self._state_lock:
            self._on_hold = False
            future = self._dispatch_task()
            self._state_lock.notify_all()

        if future is not None:
            future.add_done_callback(self._callback)

    def _pause(self):
        """Temporarily pause execution."""
        with self._state_lock:
            self._on_hold = True
            # No need to consider dispatching a task in this case.
            self._state_lock.notify_all()

    def _wait(self):
        """ Wait atleast until all previous assignments are finished, possibly
        longer

        """
        with self._state_lock:
            while not self._idle:
                self._state_lock.wait()


    ###########################################################################
    #### Trait defaults
    ###########################################################################

    def _worker(self):
        """Worker for the _update method. """

        # Get the current context, apply then delete the delta
        with self._data_lock:
            updated_vars = set(self._context_delta.keys())
            self._suppress_events = True
            self.subcontext.update(self._context_delta)
            self._suppress_events = False
            context_delta = self._context_delta.copy()
            self._context_delta.clear()

        if not updated_vars:
            return

        try:
            self.subcontext.defer_events = True
            self.executable.execute(self.subcontext, inputs=updated_vars)
            self.subcontext.defer_events = False
        except Exception:
            # If we failed to execute, put changes back into _context_delta
            with self._data_lock:
                context_delta.update(self._context_delta)
                self._context_delta = context_delta
            raise

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

    def _defer_execution_changed(self, new):
        if new:
            self._pause()
        else:
            self._resume()

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
