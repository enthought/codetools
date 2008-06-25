import sys, unittest
from compiler import parse

from enthought.testing.api import doctest_for_module

import enthought.numerical_modeling.workflow.block.parser_ as parser_
from enthought.numerical_modeling.workflow.block.parser_ import BlockTransformer
from enthought.numerical_modeling.workflow.block.compiler_.api import parse

# Extend base class compiler.ast.Node with deep equality
import enthought.numerical_modeling.workflow.block.compiler_.ast.deep_equality

class ParserDocTestCase(doctest_for_module(parser_)):
    pass

class ParserTestCase(unittest.TestCase):

    ### Support ###############################################################

    def _parse(self, s):
        return parse(s, transformer=BlockTransformer())

    ### Tests #################################################################

    def test_import_wildcard(self):
        "Rewrite 'from foo import *'"
        code = 'from foo import *'
        new_code = BlockTransformer._rewrite_wildcard_into % 'foo'
        self.assertEqual(self._parse(code), parse(new_code))

    def test_import_from(self):
        "Leave 'from foo import a,b' unchanged"
        code = 'a = 5; from foo import b,c; print b'
        self.assertEqual(self._parse(code), parse(code))

    def test_normal_import(self):
        "Leave 'import foo' unchanged"
        code = 'a = 5; import foo, bar; print b'
        self.assertEqual(self._parse(code), parse(code))

if __name__ == '__main__':
    unittest.main(argv=sys.argv)
