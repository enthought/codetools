import unittest

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
        assert 'a' in ec
        assert 'b' in ec
        assert 'c' not in ec

        ec['a'] = 2
        ec._wait()
        assert ec['a'] == 2
        assert 'c' in ec
        assert ec['c'] == 4

        ec['a'] = 4
        ec._wait()
        assert ec['a'] == 4
        assert ec['c'] == 6

    def test_defer_execution(self):
        """ Does deferring execution work?
        """
        d = DataContext()

        ec = AsyncExecutingContext(subcontext=d, executable=ce)

        ec.defer_execution = True
        ec['a'] = 1
        assert 'c' not in ec
        ec['b'] = 2
        assert 'c' not in ec
        ec.defer_execution = False
        ec._wait()
        assert 'c' in ec
        assert ec['c'] == 3

    def test_rapid_updates(self):
        self.ec.on_trait_change(self._items_modified_fired, 'items_modified')
        for i in xrange(10):
            self.ec['a'] = i
        self.ec._wait()
        self.assertEqual(self.ec['a'], 9)

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

    def test_items_modified_fired(self):
        self.ec.on_trait_change(self._items_modified_fired, 'items_modified')
        self.ec['a'] = 6
        self.ec._wait()
        self.assertEqual(self.events[0].modified, ['a'])
        self.assertEqual(self.events[1].added, ['c'])

    def _items_modified_fired(self, event):
        self.events.append(event)


if __name__ == "__main__":
    unittest.main()
