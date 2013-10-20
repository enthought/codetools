import unittest2 as unittest
import time

from codetools.contexts.api import DataContext
from codetools.execution.executing_context import CodeExecutable
from codetools.execution.restricting_code_executable import (
        RestrictingCodeExecutable)
from codetools.execution.async_executing_context import AsyncExecutingContext

ce = CodeExecutable(code="c = a + b")
CODE = """
c = a + b
d = c + 5
f = 1 + g"""


class TestAsyncExecutingContext(unittest.TestCase):

    def setUp(self):
        self.events = []
        self.exceptions = []
        d = DataContext()
        d['a'] = 1
        d['b'] = 2
        self.ec = AsyncExecutingContext(subcontext=d, executable=ce)

    def test_basic(self):
        """ Does the basic functionality of an ExecutingContext work?
        """
        d = DataContext()
        d['a'] = 1
        d['b'] = 2
        ec = AsyncExecutingContext(subcontext=d, executable=ce)
        self.assertIn('a', ec)
        self.assertIn('b', ec)
        self.assertNotIn('c', ec)

        ec['a'] = 2
        ec._wait()
        self.assertEqual(ec['a'], 2)
        self.assertIn('c', ec)
        self.assertEqual(ec['c'], 4)

        ec['a'] = 4
        ec._wait()
        self.assertEqual(ec['a'], 4)
        self.assertEqual(ec['c'], 6)

    def test_defer_execution(self):
        """ Does deferring execution work?
        """
        d = DataContext()

        ec = AsyncExecutingContext(subcontext=d, executable=ce)

        ec.defer_execution = True
        ec['a'] = 1
        time.sleep(0.1)
        self.assertNotIn('c', ec)
        ec['b'] = 2
        time.sleep(0.1)
        self.assertNotIn('c', ec)
        ec.defer_execution = False
        ec._wait()
        self.assertIn('c', ec)
        self.assertEqual(ec['c'], 3)

    def test_rapid_updates(self):
        self.ec.on_trait_change(self._items_modified_fired, 'items_modified')
        for i in xrange(10):
            self.ec['a'] = i
        self.ec._wait()
        self.assertEqual(self.ec['a'], 9)
        self.assertEqual(self.ec['c'], 11)

    def test_execute(self):
        d = DataContext()
        d['a'] = 1
        d['b'] = 3
        d['g'] = 5
        rce = RestrictingCodeExecutable(code=CODE)
        ec = AsyncExecutingContext(subcontext=d, executable=rce)
        ec.on_trait_change(self._items_modified_fired, 'items_modified')

        ec.execute()
        ec._wait()
        self.assertEqual(self.events[0].added, ['c', 'd', 'f'])
        self.assertEqual(len(self.events), 1)

    def test_execute_for_names(self):
        """`execute_for_names()` is part of the ExecutingContext interface """

        d = DataContext()
        d['a'] = 1
        d['b'] = 3
        d['g'] = 5
        rce = RestrictingCodeExecutable(code=CODE)
        ec = AsyncExecutingContext(subcontext=d, executable=rce)
        ec.on_trait_change(self._items_modified_fired, 'items_modified')

        ec.execute_for_names(['g'])
        ec._wait()
        self.assertEqual(self.events[0].added, ['f'])

    def test_exception(self):
        ce = CodeExecutable(code="c = a + b")
        d = DataContext()
        d['a'] = 1
        d['b'] = 2
        ec = AsyncExecutingContext(subcontext=d, executable=ce)
        ec.on_trait_change(self._handle_exceptions, 'exception')
        ec.code = '1/0'
        ec._wait()
        self.assertEqual(len(self.exceptions), 1)
        self.assertEqual(ZeroDivisionError, type(self.exceptions[0]))

    def test_items_modified_fired(self):
        self.ec.on_trait_change(self._items_modified_fired, 'items_modified')
        self.ec['a'] = 6
        self.ec._wait()
        self.assertEqual(self.events[0].modified, ['a'])
        self.assertEqual(self.events[1].added, ['c'])

    def _items_modified_fired(self, event):
        self.events.append(event)

    def _handle_exceptions(self, exception):
        self.exceptions.append(exception)


if __name__ == "__main__":
    unittest.main()
