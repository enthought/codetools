'''
Created on Aug 4, 2011

@author: sean
'''
from asttools.visitors import Visitor, visit_children
from asttools.visitors.symbol_visitor import get_symbols
import ast

class ConditionalSymbolVisitor(Visitor):

    def __init__(self):
        self.cond_lhs = set()
        self.all_lhs = set()
        self.seen_break = False

    visitDefault = visit_children

    @property
    def stable_outputs(self):
        return self.all_lhs - self.cond_lhs

    def visitAssign(self, node):
        ids = set()
        for target in node.targets:
            ids.update(get_symbols(target, ast.Store))

        if self.seen_break:
            self.cond_lhs.update(ids)
        else:
            self.all_lhs.update(ids)

    def visitBreak(self, node):
        self.seen_break = True

    def visitContinue(self, node):
        self.seen_break = True

    def visitFor(self, node):

        gen = ConditionalSymbolVisitor()
        for stmnt in node.body:
            gen.visit(stmnt)

        self.cond_lhs.update(gen.cond_lhs)

        outputs = gen.stable_outputs

        gen = ConditionalSymbolVisitor()
        for stmnt in node.orelse:
            gen.visit(stmnt)

        self.cond_lhs.update(gen.cond_lhs)

        orelse_outputs = gen.stable_outputs


        self.all_lhs.update(outputs.intersection(orelse_outputs))
        self.all_lhs.update(outputs.intersection(orelse_outputs))


        self.cond_lhs.update(outputs.symmetric_difference(orelse_outputs))

    visitWhile = visitFor

    def visitIf(self, node):

        gen = ConditionalSymbolVisitor()
        for stmnt in node.body:
            gen.visit(stmnt)

        if gen.seen_break:
            self.seen_break = True

        self.cond_lhs.update(gen.cond_lhs)

        outputs = gen.stable_outputs

        gen = ConditionalSymbolVisitor()
        for stmnt in node.orelse:
            gen.visit(stmnt)

        self.cond_lhs.update(gen.cond_lhs)

        orelse_outputs = gen.stable_outputs

        self.all_lhs.update(outputs.intersection(orelse_outputs))
        self.all_lhs.update(outputs.intersection(orelse_outputs))


        self.cond_lhs.update(outputs.symmetric_difference(orelse_outputs))

def conditional_lhs(node):
    '''
    Group outputs into contitional and stable
    :param node: ast node 
    
    :returns: tuple of (contitional, stable)
    
    '''

    gen = ConditionalSymbolVisitor()
    gen.visit(node)
    return gen.cond_lhs - gen.all_lhs, gen.all_lhs - gen.cond_lhs

if __name__ == '__main__':

    source = '''
while k:
    a = 1
    b = 1
    break
    d = 1
else:
    a =2
    c= 3
    d = 1
    '''

    print conditional_lhs(ast.parse(source))


