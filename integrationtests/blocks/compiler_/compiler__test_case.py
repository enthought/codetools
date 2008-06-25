import sys, unittest
from compiler.ast import Assign, Stmt, Module
from copy import copy

from enthought.testing.api import doctest_for_module

import enthought.numerical_modeling.workflow.block.compiler_.compiler_ \
    as compiler_
from enthought.numerical_modeling.workflow.block.compiler_.api import \
    compile_ast, parse

class CompilerDocTestCase(doctest_for_module(compiler_)):
    pass

class CompilerTestCase(unittest.TestCase):

    def _base(self, code_str, env={}, error=None):
        if error:
            self.assertRaises(error, lambda: self._base(code_str, env))
        else:
            env1, env2 = copy(env), copy(env)
            exec compile_ast(parse(code_str)) in env1
            exec code_str in env2
            self.assertEqual(env1, env2)

    def test_compile(self):
        'compile'
        self._base('a=4')
        self._base('a=b', error=NameError)
        self._base('a=f(z); b=a+1', { 'f':len, 'z':'asdf' })
        self._base('a=f(z); a=a+1', { 'f':len, 'z':'asdf' })
        self._base('+-3j90', error=SyntaxError)

if __name__ == '__main__':
    unittest.main(argv=sys.argv)
