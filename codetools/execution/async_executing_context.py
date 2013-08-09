#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

import contextlib
import threading

from concurrent.futures import Executor, Future
from concurrent.futures import ThreadPoolExecutor

from traits.api import (Instance, Dict, Event, Code, Any, on_trait_change,
        Bool, Undefined, Supports)

from codetools.contexts.data_context import DataContext
from .executing_context import ExecutingContext
from .interfaces import IListenableContext
from .restricting_code_executable import RestrictingCodeExecutable


class AsyncExecutingContext(ExecutingContext):
    """Sequential, threaded pipeline for execution of a Block.

    This uses a (possibly shared) Executor to asynchronously execute a block
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
    subcontext = Supports(IListenableContext, factory=DataContext,
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

    _full_update = Bool(False)

    ###########################################################################
    #### AsyncExecutingContext Interface
    ###########################################################################

    def execute(self):
        """Update the context by executing the full block.
        This executes asynchronously.

        """
        self._full_update = True
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

    # A lock for state changes.
    _state_lock = Instance(threading.Condition, ())

    # State flag: true iff execution is currently deferred.
    _execution_deferred = Bool(False)

    # Flag indicating whether there's a need to do a new update at
    # some point.
    _update_pending = Bool(False)

    # The current Future instance, or None.
    _future = Instance(Future)

    @contextlib.contextmanager
    def _update_state(self):
        """Helper for state updates.

        Applies the state update in the body of the associated with block;
        starts a new future execution if necessary, and notifies all listeners
        of the state change.

        """
        with self._state_lock:
            yield
            submit_new = (
                self._future is None and self._update_pending and
                not self._execution_deferred
            )
            if submit_new:
                self._update_pending = False
                self._future = self.executor.submit(self._worker)
            self._state_lock.notify_all()

        if submit_new:
            self._future.add_done_callback(self._callback)

    # Transition methods.

    def _update(self):
        """Update based on changes in _context_delta."""
        with self._update_state():
            self._update_pending = True

    def _callback(self, future):
        """Callback for the _worker"""
        with self._update_state():
            exception = future.exception()
            if exception is not None:
                self.exception = exception
            self._future = None

    def _pause(self):
        """Temporarily pause execution."""
        with self._update_state():
            self._execution_deferred = True

    def _resume(self):
        """Resume execution."""
        with self._update_state():
            self._execution_deferred = False

    def _wait(self):
        """Wait until all previous assignments are finished, possibly longer."""
        with self._state_lock:
            while self._future is not None:
                self._state_lock.wait()

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

        if not updated_vars and not self._full_update:
            # don't execute if no context delta or full update requested
            return

        if self._full_update:
            # signal to self.executable that we want the unrestricted block to
            # be executed and then clear the flag
            updated_vars = []
            self._full_update = False

        try:
            self.subcontext.defer_events = True
            self.executable.execute(self.subcontext, inputs=updated_vars)
            self.subcontext.defer_events = False
        except Exception:
            self.subcontext.defer_events = False
            # If we failed to execute, put changes back into _context_delta
            with self._data_lock:
                context_delta.update(self._context_delta)
                self._context_delta = context_delta
            raise

    ###########################################################################
    #### Trait defaults
    ###########################################################################

    def _executor_default(self):
        return ThreadPoolExecutor(max_workers=2)

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
