"""Text block execution with multiple exceptions"""
import unittest
from enthought.blocks.block import Block, CompositeException
from enthought.blocks.api import func2str

@func2str
def block():
    from math import log
    a=-1
    b=2
    c=log(a)
    d=3

@func2str
def block2_():
    e=log(a)
    f=4

block2 = block + block2_


class ErrorContinueTest(unittest.TestCase):
    def test_single_exception(self):
        ctx = {}
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
    
        
