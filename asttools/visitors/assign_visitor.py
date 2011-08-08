'''
Created on Aug 4, 2011

@author: sean
'''
from asttools.visitors import Visitor, visit_children, dont_visit
from asttools.visitors.symbol_visitor import get_symbols
import ast

class MutableValues(Visitor):

    def __init__(self):
        self.modified = set()

    visitModule = visit_children
    visitPass = visit_children

    visitClassDef = dont_visit
    visitFunctionDef = dont_visit

    def visitAssign(self, node):
        pass

    def visitAugAssign(self, node):
        self.modified.update(get_symbols(node.target))



class RLValueVisitor(Visitor):

    def __init__(self):
        self.rhs = set()
        self.lhs = set()

    visitModule = visit_children
    visitPass = visit_children

    def visitWith(self, node):
        self.rhs.update(get_symbols(node.context_expr, ast.Load))
        
        if node.optional_vars:
            self.lhs.update(get_symbols(node.optional_vars, ast.Load))

        for child in node.body:
            self.visit(child)


    def visitImport(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.lhs.add(name)

    def visitImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.lhs.add(name)



    def visitClassDef(self, node):
        for decorator in node.decorator_list:
            self.rhs(get_symbols(decorator, ast.Load))
        self.lhs.add(node.name)

    def visitFunctionDef(self, node):
        for decorator in node.decorator_list:
            self.rhs(get_symbols(decorator, ast.Load))
        self.lhs.add(node.name)

    def visitAssign(self, node):
        for target in node.targets:
            self.lhs.update(get_symbols(target, ast.Store))

        self.rhs.update(get_symbols(node.value, ast.Load))

    def visitAugAssign(self, node):

        self.lhs.update(get_symbols(node.target, ast.Store))

        self.rhs.update(get_symbols(node.target, ast.Load))
        self.rhs.update(get_symbols(node.value, ast.Load))

    def visitWhile(self, node):
        self.rhs.update(get_symbols(node.test, ast.Load))

        for stmnt in node.body:
            self.visit(stmnt)

        for stmnt in node.orelse:
            self.visit(stmnt)

    def visitFor(self, node):
        self.rhs.update(get_symbols(node.iter, ast.Store))

        self.lhs.update(get_symbols(node.target, ast.Load))

        for stmnt in node.body:
            self.visit(stmnt)

        for stmnt in node.orelse:
            self.visit(stmnt)

    def visitExpr(self, node):
        self.rhs.update(get_symbols(node.value, ast.Load))

    def visitIf(self, node):
        self.rhs.update(get_symbols(node.test, ast.Load))

        for stmnt in node.body:
            self.visit(stmnt)

        for stmnt in node.orelse:
            self.visit(stmnt)

    def visitRaise(self, node):
        return



def lhs(node):
    visitor = RLValueVisitor()
    if isinstance(node, (list, tuple)):
        for child in node:
            visitor.visit(child)
    else:
        visitor.visit(node)
    return visitor.lhs

def rhs(node):
    visitor = RLValueVisitor()
    if isinstance(node, (list, tuple)):
        for child in node:
            visitor.visit(child)
    else:
        visitor.visit(node)
    return visitor.rhs
