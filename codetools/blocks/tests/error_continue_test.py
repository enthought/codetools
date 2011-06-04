"""Text block execution with multiple exceptions"""
import unittest
from codetools.blocks.block import Block, CompositeException
from codetools.blocks.api import func2str

def raises_valuerror():
    raise ValueError

@func2str
def block():
    a=-1
    b=2
    c=raises_valuerror()
    d=3

@func2str
def block2_():
    e=log(a)
    f=4

block2 = block + block2_


class ErrorContinueTest(unittest.TestCase):
    def test_single_exception(self):
        ctx = dict(raises_valuerror=raises_valuerror)
        b = Block(block)
        try:
            b.execute(ctx, continue_on_errors=True)
            assert False #We should have thrown
        except Exception, e:
            assert isinstance(e, ValueError)
            assert ctx.has_key('d')
        return

    def test_multi_exception(self):
        ctx = {}
        b = Block(block2)
        try:
            b.execute(ctx, continue_on_errors=True)
            assert False #We should have thrown
        except Exception, e:
            assert isinstance(e, CompositeException)
            assert len(e.exceptions) == 2
        return


