from decompile.instructions import make_module, make_function
from compiler.pycodegen import FunctionCodeGenerator, ModuleCodeGenerator

import _ast


def decompile_func(func):

    code = getattr(func, 'func_code', None)
    if code is None:
        raise TypeError('can not get ast from %r' % (func,))


    if func.func_defaults:
        default_names = code.co_varnames[:code.co_argcount][-len(func.func_defaults):]
    else:
        default_names = []
    defaults = [_ast.Name(id='%s_default' % name, ctx=_ast.Load() , lineno=0, col_offset=0) for name in default_names]
    ast_node = make_function(code, defaults=defaults, lineno=code.co_firstlineno)

    return ast_node

def compile_func(ast_node, filename, globals, **defaults):

    funcion_name = ast_node.name
    module = _ast.Module(body=[ast_node])

    ctx = {'%s_default' % key : arg for key, arg in defaults.items()}

    code = compile(module, filename, 'exec')

    eval(code, globals, ctx)

    function = ctx[funcion_name]

    return function


