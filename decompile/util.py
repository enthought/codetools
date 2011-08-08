'''
Created on Jul 15, 2011

@author: sean
'''

import _ast
import sys


def ast_keys(node):
    return node._fields

def ast_values(node):
    return [getattr(node, field, None) for field in node._fields]

def ast_items(node):
    return [(field, getattr(node, field, None)) for field in node._fields]


def print_ast(ast, indent='  ', stream=sys.stdout, initlevel=0, newline='\n'):

    rec_node2(ast, initlevel, indent, stream.write, assign=None, newline=newline)
    stream.write('\n')

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


def rec_node2(node, level, indent, write, assign, newline):
    "Recurse through a node, pretty-printing it."
    pfx = indent * level

    node_depth = depth(node)
    if node_depth < 2:
        indent = newline = ''

    if isinstance(node, _ast.AST):
        write(pfx)
        if assign:
            write('%s=%s(' % (assign, node.__class__.__name__))
        else:
            write('%s(' % (node.__class__.__name__))

        i = 0
        for key, value in ast_items(node):
            if i != 0:
                write(', ')
            i += 1
            write(newline)
            if isinstance(value, (list, tuple)):
                write('%s=[%s' % (key, newline))
                for child in value:
                    rec_node2(child, level + 2, indent, write, None, newline)
                    write(', ')
                write(']')
            else:
                rec_node2(value, level + 1, indent, write, key, newline)

        write(newline)
        write(pfx)

        attrs = ['%s=%r' % (attr, getattr(node, attr, '?'))for attr in node._attributes]
        if attrs:
            write(', ' +', '.join(attrs))
        write(')')

    else:
        write(pfx)
        if assign:
            write('%s=%r' % (assign, node,))
        else:
            write('%r' % (node,))

def cmp_tree(left, right):

    if type(left) != type(right):
        return False

    if isinstance(left, (list, tuple)):
        if len(left) != len(right):
            return False
        for l, r in zip(left, right):
            if not cmp_tree(l, r):
                return False

    elif not isinstance(left, _ast.AST):
        return left == right
    else:
        lkeys = ast_keys(left)
        rkeys = ast_keys(right)

        if lkeys != rkeys:
            return False

        for key in lkeys:
            lvalue = getattr(left, key)
            rvalue = getattr(right, key)

            result = cmp_tree(lvalue, rvalue)
            if not result:
                return False

    return True



