'''
Created on Aug 3, 2011

@author: sean
'''
from asttools.visitors import Visitor
import ast

class SymbolVisitor(Visitor):
    def __init__(self, ctx_types=(ast.Load, ast.Store)):
        self.ctx_types = ctx_types

    def visitDefault(self, node):
        ids = set()
        for child in self.children(node):

            if isinstance(child, (tuple, list)):
                for item in child:
                    ids.update(self.visit(item))

            elif isinstance(child, ast.AST):
                ids.update(self.visit(child))

        return ids

    def visitName(self, node):
        if isinstance(node.ctx, self.ctx_types):
            return {node.id}
        else:
            return {}


def get_symbols(node, ctx_types=(ast.Load, ast.Store)):
    gen = SymbolVisitor(ctx_types)
    return gen.visit(node)
