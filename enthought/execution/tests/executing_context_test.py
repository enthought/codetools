
from enthought.block_canvas.context.api import DataContext

from enthought.block_canvas.execution.executing_context import (CodeExecutable,
    ExecutingContext)


ce = CodeExecutable(code="c = a + b")


def test_basic():
    """ Does the basic functionality of an ExecutingContext work?
    """
    d = DataContext()
    d['a'] = 1
    d['b'] = 2
    ec = ExecutingContext(subcontext=d, executable=ce)
    assert 'a' in ec
    assert 'b' in ec
    assert 'c' not in ec

    ec['a'] = 2
    assert ec['a'] == 2
    assert 'c' in ec
    assert ec['c'] == 4

    ec['a'] = 4
    assert ec['a'] == 4
    assert ec['c'] == 6

def test_defer_execution():
    """ Does deferring execution work?
    """
    d = DataContext()
    ec = ExecutingContext(subcontext=d, executable=ce)

    ec.defer_execution = True
    ec['a'] = 1
    assert 'c' not in ec
    ec['b'] = 2
    assert 'c' not in ec
    ec.defer_execution = False
    assert 'c' in ec
    assert ec['c'] == 3

def test_code_executable():
    """ Does a CodeExecutable work correctly?
    """
    d = dict(a=1, b=2)
    ce.execute(d)
    assert 'c' in d
    assert d['c'] == 3
