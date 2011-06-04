# (Needs python 2.5. That is, we don't use this module yet)

import _ast # (New in python 2.5)

def eq(a,b):
    '(A quick hack)'
    if isinstance(a, _ast.AST) and isinstance(b, _ast.AST):
        return type(a) == type(b) and \
               (a._fields is None or \
                all([ eq(getattr(a,f), getattr(b,f)) for f in a._fields ]))
    elif isinstance(a, list) and isinstance(b, list):
        return all([ eq(aa,bb) for (aa,bb) in zip(a,b) ])
    else:
        return a == b

def to_tree(x):
    if isinstance(x, _ast.AST):
        if x._fields is not None:
            fields = x._fields
        else:
            fields = []
        return tuple([x.__class__.__name__] +
                     [ to_tuple(getattr(x,f)) for f in fields ])
    elif isinstance(x, list):
        return map(to_tuple, x)
    else:
        return x

all = lambda l: False not in map(bool, l)
any = lambda l: True in map(bool, l)
