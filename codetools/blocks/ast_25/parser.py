import _ast # (New in python 2.5)
from cStringIO import StringIO

from unparse_ import Unparser

def parse(s, filename='<string>', mode='exec'):
    return compile(s, filename, mode, _ast.PyCF_ONLY_AST)

def unparse(ast):
    s = StringIO()
    Unparser(ast, s)
    return s.getvalue()
