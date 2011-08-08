'''
Created on Jul 14, 2011

@author: sean
'''
from decompile.simple_instructions import SimpleInstructions
from decompile.control_flow_instructions import CtrlFlowInstructions
import _ast
from asttools import print_ast

def pop_doc(stmnts):

    doc = pop_assignment(stmnts, '__doc__')

    assert isinstance(doc, _ast.Str) or doc is None

    return doc

def pop_assignment(stmnts, name):

    for i in range(len(stmnts)):
        stmnt = stmnts[i]
        if isinstance(stmnt, _ast.Assign) and len(stmnt.targets) == 1 \
            and isinstance(stmnt.targets[0], _ast.Name) \
            and isinstance(stmnt.targets[0].ctx, _ast.Store):
            if stmnt.targets[0].id == name:
                stmnts.pop(i)
                return stmnt.value

    return None

def pop_return(stmnts):

    ns = len(stmnts)
    for i in range(ns - 1, -1, -1):
        stmnt = stmnts[i]
        if isinstance(stmnt, _ast.Return):
            return stmnts.pop(i)
    return None


def make_module(code):
        from decompile.disassemble import disassemble
        instructions = Instructions(disassemble(code))
        stmnts = instructions.stmnt()

        doc = pop_doc(stmnts)
        pop_return(stmnts)

#        stmnt = ast.Stmt(stmnts, 0)

        if doc is not None:
            stmnts = [_ast.Expr(value=doc, lineno=doc.lineno, col_offset=0)] + stmnts

        ast_obj = _ast.Module(body=stmnts, lineno=0, col_offset=0)

        return ast_obj

def make_function(code, defaults=None, lineno=0):
        from decompile.disassemble import disassemble

        instructions = Instructions(disassemble(code))

        stmnts = instructions.stmnt()

        if code.co_flags & 2:
            vararg = None
            kwarg = None

        varnames = list(code.co_varnames[:code.co_argcount])
        co_locals = list(code.co_varnames[code.co_argcount:])

        #have var args
        if code.co_flags & 4:
            vararg = co_locals.pop(0)

        #have kw args
        if code.co_flags & 8:
            kwarg = co_locals.pop()

        args = [_ast.Name(id=argname, ctx=_ast.Param(), lineno=lineno, col_offset=0) for argname in varnames]
        args = _ast.arguments(args=args,
                              defaults=defaults if defaults else [],
                              kwarg=kwarg,
                              vararg=vararg,
                              lineno=lineno, col_offset=0
                              )
        if code.co_name == '<lambda>':
            assert len(stmnts) == 1
            assert isinstance(stmnts[0], _ast.Return)

            stmnt = stmnts[0].value
            ast_obj = _ast.Lambda(args=args, body=stmnt, lineno=lineno, col_offset=0)
        else:

            if instructions.seen_yield:
                return_ = stmnts[-1]

                assert isinstance(return_, _ast.Return)
                assert isinstance(return_.value, _ast.Name)
                assert return_.value.id == 'None'
                return_.value = None
            ast_obj = _ast.FunctionDef(name=code.co_name, args=args, body=stmnts, decorator_list=[], lineno=lineno, col_offset=0)

        return ast_obj


class StackLogger(list):
    def append(self, object):
        print '    + ',
        print_ast(object, indent='', newline='')
        print
        list.append(self, object)

    def pop(self, *index):
        value = list.pop(self, *index)
        print '    - ',
        print_ast(value, indent='', newline='')
        print
        return value


class Instructions(CtrlFlowInstructions, SimpleInstructions):

    def __init__(self, ilst, stack_items=None, jump_map=False):
        self.ilst_processed = []
        self.ilst = ilst[:]
        self.orig_ilst = ilst
        self.seen_yield = False

        if jump_map:
            self.jump_map = jump_map
        else:
            self.jump_map = {}

#        self.ast_stack = StackLogger()
        self.ast_stack = []

        if stack_items:
            self.ast_stack.extend(stack_items)

    @classmethod
    def decompile_block(cls, ilst, stack_items=None, jump_map=False):
        return Instructions(ilst, stack_items=stack_items, jump_map=jump_map)

    def stmnt(self):

        while len(self.ilst):
            instr = self.ilst.pop(0)
            self.visit(instr)

        return self.ast_stack

    def visit(self, instr):
        name = instr.opname.replace('+', '_')

        method = getattr(self, name, None)
        if method is None:
            raise AttributeError('can not handle instruction %r' % (str(instr)))

#        print ">>>", name
        method(instr)


    def make_block(self, to, inclusive=True, raise_=True):

        block = []
        while len(self.ilst):
            instr = self.ilst.pop(0)
            block.append(instr)
            if instr.i == to:
                if not inclusive:
                    instr = block.pop()
                    self.ilst.insert(0, instr)
                break
        else:
            if raise_:
                raise IndexError("no instrcution i=%s " % (to,))

        return block

    def MAKE_FUNCTION(self, instr):

        code = self.ast_stack.pop()

        ndefaults = instr.oparg

        defaults = []
        for i in range(ndefaults):
            defaults.insert(0, self.ast_stack.pop())

        function = make_function(code, defaults, lineno=instr.lineno)

        self.ast_stack.append(function)

    def LOAD_LOCALS(self, instr):
        self.ast_stack.append('LOAD_LOCALS')

    def BUILD_CLASS(self, instr):

        call_func = self.ast_stack.pop()

        assert isinstance(call_func, _ast.Call)

        func = call_func.func

        assert isinstance(func, _ast.FunctionDef)

        code = func.body
        pop_assignment(code, '__module__')
        doc = pop_doc(code)

        if doc is not None:
            code.insert(0, _ast.Expr(value=doc, lineno=doc.lineno, col_offset=0))

        ret = code.pop()

        assert isinstance(ret, _ast.Return) and ret.value == 'LOAD_LOCALS'

        bases = self.ast_stack.pop()

        assert isinstance(bases, _ast.Tuple)
        bases = bases.elts
        name = self.ast_stack.pop()

        class_ = _ast.ClassDef(name=name, bases=bases, body=code, decorator_list=[],
                               lineno=instr.lineno, col_offset=0)

        self.ast_stack.append(class_)

    def LOAD_CLOSURE(self, instr):
        self.ast_stack.append('CLOSURE')

    def MAKE_CLOSURE(self, instr):
        return self.MAKE_FUNCTION(instr)

