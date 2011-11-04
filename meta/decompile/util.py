'''
Created on Jul 15, 2011

@author: sean
'''

import _ast
import sys
py3 = sys.version_info.major >= 3

def ast_keys(node):
    return node._fields

def ast_values(node):
    return [getattr(node, field, None) for field in node._fields]

def ast_items(node):
    return [(field, getattr(node, field, None)) for field in node._fields]


def depth(node):
    return len(flatten(node))

def flatten(node):

    result = []
    if isinstance(node, _ast.AST):
        for value in ast_values(node):
            result.extend(flatten(value))
    elif isinstance(node, (list, tuple)):
        for child in node:
            result.extend(flatten(child))
    else:
        result.append(node)

    return result

class Python2(object):
    @staticmethod
    def py2op(func):
        return func

def py3op(func):
    if py3:
        
        func.py2op = lambda _:func
        return func
    else:
        return Python2

class Python3(object):
    @staticmethod
    def py3op(func):
        return func

def py2op(func):
    if not py3:
        func.py3op = lambda _:func
        return func
    else:
        return Python3
