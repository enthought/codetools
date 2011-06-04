'''Extensions to the standard 'compiler' module'''

import compiler
from compiler import pycodegen
from compiler.ast import Expression, Module
from compiler.transformer import Transformer
from copy import copy
import sys

# (Copied from python2.4/compiler/transformer.py)
def parse(buf, mode="exec", transformer=None):
    'Extends compiler.parse to take a transformer.'
    if transformer is None:
        transformer = Transformer()
    if mode == "exec" or mode == "single":
        # Since the parser gives a SyntaxError with the 'with' keyword,
        # add the import along with the buffer, then remove it. The lineno
        # on the ast nodes must also be adjusted
        py_version = sys.version_info
        py_version = int(py_version[0])+0.1*int(py_version[1])
        if py_version < 2.6:
            new_buf = 'from __future__ import with_statement\n' + buf
            ast = transformer.parsesuite(new_buf)
            ast.node.nodes = ast.node.nodes[1:]
            for node in ast.node.nodes:
                if node.lineno is not None:
                    node.lineno -= 1
            return ast
        return transformer.parsesuite(buf)
    elif mode == "eval":
        return transformer.parseexpr(buf)
    else:
        raise ValueError("compile() arg 3 must be"
                         " 'exec' or 'eval' or 'single'")

def compile_ast(ast, filename='<ast>', mode='exec'):
    "Extends compiler.compile to understand ASTs from compiler.ast."
    ast = copy(ast)

    modes = {
        'eval'   : pycodegen.ExpressionCodeGenerator,
        'exec'   : pycodegen.ModuleCodeGenerator,
        'single' : pycodegen.InteractiveCodeGenerator,
    }

    # (Copied from compiler.pygencode.Interactive)
    compiler.misc.set_filename(filename, ast)
    compiler.syntax.check(ast)
    return modes[mode](ast).getCode()

def eval_ast(ast, filename='<ast>', *contexts):
    "Extends 'eval' to understand ASTs from compiler.ast."
    assert isinstance(ast, Expression)
    return eval(compile_ast(ast, filename=filename, mode='eval'), *contexts)

def exec_ast(ast, filename='<ast>', globals=None, locals=None):
    "Extends 'exec' to understand ASTs from compiler.ast."
    assert isinstance(ast, Module)

    code = compile_ast(ast, filename=filename, mode='exec')

    # (exec doesn't take *args...)
    if globals is None:
        exec code
    elif locals is None:
        exec code in globals
    else:
        exec code in globals, locals
