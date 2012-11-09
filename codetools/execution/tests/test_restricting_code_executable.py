import unittest

from codetools.execution.executing_context import ExecutingContext

from fei.testing.test_assistant import TestAssistant
from fei.edx.model.block_pipeline.restricting_code_executable import (
        RestrictingCodeExecutable)

CODE = """aa = 2 * a
bb = 2 * b
c = a + b + aa + bb
"""


class TestRestrictingCodeExecutable(unittest.TestCase, TestAssistant):

    def setUp(self):
        self.restricting_exec = RestrictingCodeExecutable(code=CODE)
        self.context = {'a': 1, 'b': 10}

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
        self.assertEqual(self.restricting_exec.block.codestring, CODE)

    def test_init_with_code_error_fails(self):
        with self.assertRaises(SyntaxError):
            restricting_exec = RestrictingCodeExecutable(".,.")

    def test_init_without_code_fails(self):
        with self.assertRaises(ValueError):
            restricting_exec = RestrictingCodeExecutable()

    def test_api_compatibility(self):
        executing_context = ExecutingContext(executable=self.restricting_exec,
                subcontext=self.context)
        self.assertIs(self.context, executing_context.subcontext.subcontext)
        executing_context.execute_for_names(None)
        with self.assertTraitChanges(executing_context, 'items_modified'):
            executing_context['bb'] = 5
        expected_context = {'a': 1, 'b': 10, 'aa': 2, 'bb': 5, 'c': 18}
        self.assertEqual(self.context, expected_context)


if __name__ == '__main__':
    unittest.main()
