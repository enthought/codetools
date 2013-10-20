import unittest2 as unittest

from codetools.execution.executing_context import ExecutingContext
from codetools.execution.restricting_code_executable import (
        RestrictingCodeExecutable)

CODE = """aa = 2 * a
bb = 2 * b
c = a + b + aa + bb
"""


class TestRestrictingCodeExecutable(unittest.TestCase):

    def setUp(self):
        self.restricting_exec = RestrictingCodeExecutable(code=CODE)
        self.context = {'a': 1, 'b': 10}
        self.events = []

    def test_execute(self):
        self.restricting_exec.execute(self.context)
        expected_context = {'a': 1, 'b': 10, 'aa': 2, 'bb': 20, 'c': 33}
        self.assertEqual(self.context, expected_context)

    def test_restrict_on_inputs(self):
        context = {'a': 1, 'b': 10, 'bb': 100}
        self.restricting_exec.execute(context, inputs=['a'])
        #Check if `bb` was incorrectly overwritten by the codeblock
        self.assertEqual(context['bb'], 100)

    def test_restrict_on_outputs(self):
        context = {'b': 10, 'bb': 100}
        self.restricting_exec.execute(context, outputs=['bb'])
        self.assertEqual(context, {'b': 10, 'bb': 20})

    def test_code_exists(self):
        self.assertEqual(self.restricting_exec.code, CODE)
        self.assertEqual(self.restricting_exec._block.codestring, CODE)

    def test_code_changing(self):
        self.restricting_exec.on_trait_change(self._change_detect, '_block')
        self.restricting_exec.code = "c = a + b"
        self.assertEqual(self.events, ['fired'])

    def test_api_compatibility(self):
        executing_context = ExecutingContext(executable=self.restricting_exec,
                subcontext=self.context)
        self.assertIs(self.context, executing_context.subcontext.subcontext)
        executing_context.execute_for_names(None)
        executing_context.on_trait_change(self._change_detect, 'items_modified')
        executing_context['bb'] = 5
        self.assertEqual(self.events, ['fired', 'fired'])
        expected_context = {'a': 1, 'b': 10, 'aa': 2, 'bb': 5, 'c': 18}
        self.assertEqual(self.context, expected_context)

    def _change_detect(self):
        self.events.append('fired')


if __name__ == '__main__':
    unittest.main()
