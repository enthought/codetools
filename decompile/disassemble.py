'''
Created on Jul 14, 2011

@author: sean
'''
from opcode import *
from dis import findlabels, findlinestarts
import types

class Instruction(object):

    def __init__(self, i= -1, op=None, lineno=None):
        self.i = i
        self.op = op
        self.lineno = lineno
        self.oparg = None
        self.arg = None
        self.extended_arg = 0
        self.linestart = False

    @property
    def opname(self):
        return opname[self.op]
    @property
    def to(self):
        if self.op in hasjrel:
            return self.arg
        elif self.op in hasjabs:
            return self.oparg
        else:
            raise Exception("this is not a jump op (%s)" % (self.opname,))

    def __repr__(self):
        res = '<%s(%i)' % (opname[self.op], self.i,)

        if self.arg is not None:
            res += ' arg=%r' % (self.arg,)
        elif self.oparg is not None:
            res += ' oparg=%r' % (self.oparg,)
        return res + '>'

    def __str__(self):
        result = []

        if self.linestart:
            result.append("%3d" % self.lineno)
        else:
            result.append("   ")

        if self.lasti:
            result.append('-->')
        else:
            result.append('   ')

        if self.label:
            result.append('>>')
        else:
            result.append('  ')

        result.append(repr(self.i).rjust(4))

        result.append(opname[self.op].ljust(20))

        if self.op >= HAVE_ARGUMENT:

            result.append(repr(self.oparg).rjust(5))
            if self.op in hasconst:
                result.append('(' + repr(self.arg) + ')')
            elif self.op in hasname:
                result.append('(' + repr(self.arg) + ')')
            elif self.op in hasjrel:
                result.append('(to ' + repr(self.arg) + ')')
            elif self.op in haslocal:
                result.append('(' + repr(self.arg) + ')')
            elif self.op in hascompare:
                result.append('(' + repr(self.arg) + ')')
            elif self.op in hasfree:
                result.append('(' + repr(self.arg) + ')')
        return ' '.join(result)


def disassemble(co, lasti= -1):
    """Disassemble a code object."""

    instructions = []
    code = co.co_code
    labels = findlabels(code)
    linestarts = dict(findlinestarts(co))
    n = len(code)
    i = 0
    extended_arg = 0
    lineno = 0
    free = None
    while i < n:
        c = code[i]
        op = ord(c)
        if i in linestarts:
            lineno = linestarts[i]

        instr = Instruction(i=i, op=op, lineno=lineno)
        instr.linestart = i in linestarts
        instructions.append(instr)

        if i == lasti:
            instr.lasti = True
        else:
            instr.lasti = False

        if i in labels:
            instr.label = True
        else:
            instr.label = False

        i = i + 1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i + 1]) * 256 + extended_arg
            instr.oparg = oparg
            extended_arg = 0
            i = i + 2
            if op == EXTENDED_ARG:
                extended_arg = oparg * 65536L
            instr.extended_arg = extended_arg
            if op in hasconst:
                instr.arg = co.co_consts[oparg]
            elif op in hasname:
                instr.arg = co.co_names[oparg]
            elif op in hasjrel:
                instr.arg = i + oparg
            elif op in haslocal:
                instr.arg = co.co_varnames[oparg]
            elif op in hascompare:
                instr.arg = cmp_op[oparg]
            elif op in hasfree:
                if free is None:
                    free = co.co_cellvars + co.co_freevars
                instr.arg = free[oparg]

    return instructions


def print_code(co, lasti= -1, level=0):
    """Disassemble a code object."""
    code = co.co_code
    labels = findlabels(code)
    linestarts = dict(findlinestarts(co))
    n = len(code)
    i = 0
    extended_arg = 0
    free = None
    while i < n:
        have_inner = False
        c = code[i]
        op = ord(c)

        if i in linestarts:
            if i > 0:
                print
            print '|              |' * level,
            print "%3d" % linestarts[i],
        else:
            print '|              |' * level,
            print '   ',

        if i == lasti: print '-->',
        else: print '   ',
        if i in labels: print '>>',
        else: print '  ',
        print repr(i).rjust(4),
        print opname[op].ljust(20),
        i = i + 1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i + 1]) * 256 + extended_arg
            extended_arg = 0
            i = i + 2
            if op == EXTENDED_ARG:
                extended_arg = oparg * 65536L
            print repr(oparg).rjust(5),
            if op in hasconst:

                print '(' + repr(co.co_consts[oparg]) + ')',
                if type(co.co_consts[oparg]) == types.CodeType:
                    have_inner = co.co_consts[oparg]


            elif op in hasname:
                print '(' + co.co_names[oparg] + ')',
            elif op in hasjrel:
                print '(to ' + repr(i + oparg) + ')',
            elif op in haslocal:
                print '(' + co.co_varnames[oparg] + ')',
            elif op in hascompare:
                print '(' + cmp_op[oparg] + ')',
            elif op in hasfree:
                if free is None:
                    free = co.co_cellvars + co.co_freevars
                print '(' + free[oparg] + ')',
        print

        if have_inner is not False:
            print_code(have_inner, level=level + 1)
