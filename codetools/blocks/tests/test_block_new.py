'''
Created on Aug 5, 2011

@author: sean
'''
import unittest
from codetools.blocks.smart_code import SmartCode
from asttools.tests import assert_ast_eq
import ast
from os.path import exists
from codetools.blocks.tests import assert_block_eq

class Test(unittest.TestCase):


    def test_init(self):

        with self.assertRaises(TypeError):
            SmartCode(source=True, file=True)

    def test_ast(self):
        source = 'a = b'
        block = SmartCode(source=source)

        mod = ast.parse(source)

        assert_ast_eq(self, block.ast, ast.parse(source))

        self.assertEqual(block.code.co_code, compile(mod, '<unknown>', 'exec').co_code)

    def test_write_file(self):
        source = 'a = b'
        block = SmartCode(source=source)

        self.assertTrue(exists(block.path))

        self.assertEqual(open(block.path).read(), source)


    def test_codestring(self):
        source = 'a = b; c = d'
        block = SmartCode(source=source)
        self.assertMultiLineEqual(block.codestring, '\na = b\nc = d\n\n')
        
        sub_block = block.restrict(outputs=['a'])
        self.assertMultiLineEqual(sub_block.codestring, '\na = b\n\n')

        sub_block = block.restrict(outputs=['c'])
        self.assertMultiLineEqual(sub_block.codestring, '\nc = d\n\n')

    def test_dependents(self):

        source = 'a = b; c = d'
        block = SmartCode(source=source)

        self.assertEqual(block.depends_on(('b', 'd')), set(['a', 'b', 'c', 'd']))
        self.assertEqual(block.depends_on(('b',)), set(['a', 'b']))
        self.assertEqual(block.depends_on(('d',)), set(['c', 'd']))

        self.assertEqual(block.dependent_on(('b', 'd')), set(['b', 'd']))

        self.assertEqual(block.dependent_on(('a', 'c')), set(['a', 'b', 'c', 'd']))
        self.assertEqual(block.dependent_on(('a',)), set(['a', 'b']))
        self.assertEqual(block.dependent_on(('c',)), set(['c', 'd']))

    def test_restrict(self):
        source = 'a = b; c = d'
        block = SmartCode(source=source)

        b0 = SmartCode(' ')
        b2 = SmartCode('a = b')
        b3 = SmartCode('c = d')
        assert_block_eq(self, block.restrict(inputs=('b', 'd')), block)
        assert_block_eq(self, block.restrict(inputs=('b')), b2)
        assert_block_eq(self, block.restrict(inputs=('d')), b3)

        assert_block_eq(self, block.restrict(outputs=('b', 'd')), b0)

        assert_block_eq(self, block.restrict(outputs=('a', 'c')), block)
        assert_block_eq(self, block.restrict(outputs=('a')), b2)
        assert_block_eq(self, block.restrict(outputs=('c')), b3)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_init']
    unittest.main()
