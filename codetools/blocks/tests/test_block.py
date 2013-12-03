"""Tests for the Block class."""

from nose.tools import assert_equal, assert_raises

from codetools.blocks.api import Block
from codetools.contexts.api import DataContext


def test_basic_01():
    """Test basic use of a Block."""
    code = 'x = 100\ny = x + 1'
    b = Block(code)
    assert_equal(b.inputs, set([]))
    assert_equal(b.outputs, set(['x','y']))
    assert_equal(b.const_assign, (set(['x']), ['x = 100']))

    names = dict()
    b.execute(names)
    assert_equal(sorted(names), ['x', 'y'])
    assert_equal(names['x'], 100)
    assert_equal(names['y'], 101)

def test_basic_02():
    """Another test of the basic use of a Block."""
    code = 'y = x + 1'
    b = Block(code)
    assert_equal(b.inputs, set(['x']))
    assert_equal(b.outputs, set(['y']))

    names = dict(x=100)
    b.execute(names)
    assert_equal(sorted(names), ['x', 'y'])
    assert_equal(names['x'], 100)
    assert_equal(names['y'], 101)

def test_restrict_inputs():
    """Test a basic use of the restrict(inputs=(...)) method."""
    code = 'x = a + b\ny = b - c\nz = c**2'
    b = Block(code)
    assert_equal(b.inputs, set(['a','b','c']))
    assert_equal(b.outputs, set(['x','y','z']))

    br = b.restrict(inputs=('a',))
    names = dict(a=100, b=200)
    br.execute(names)
    assert_equal(sorted(names), ['a', 'b', 'x'])
    assert_equal(names['a'], 100)
    assert_equal(names['b'], 200)
    assert_equal(names['x'], 300)

def test_restrict_outputs():
    """Test a basic use of the restrict(outputs=(...)) method."""
    code = 'x = a + b\ny = b - c\nz = c**2'
    b = Block(code)

    br = b.restrict(outputs=('z',))
    names = dict(c=5)
    br.execute(names)
    assert_equal(sorted(names), ['c', 'z'])
    assert_equal(names['c'], 5)
    assert_equal(names['z'], 25)

def test_restricted_empty_inputs():
    """Check that restrict(inputs=()) raises a ValueError."""
    code = 'x = a + b\ny = b - c\nz = c**2'
    b = Block(code)
    assert_raises(ValueError, b.restrict, inputs=())

def test_restricted_empty_outputs():
    """Check that restrict(outputs=()) raises a ValueError."""
    code = 'x = a + b\ny = b - c\nz = c**2'
    b = Block(code)
    assert_raises(ValueError, b.restrict, outputs=())

def test_impure_execute():
    code="""
import os  # module and function names are discarded by default.
def ff():
    global y  # will not be retained but will be available in the code block.
    y = a + x
    b.append(4)
x = a
b.append(3)
ff()
z = y
_x = x  # names beginning with underscore are discarded by default
a = 99
"""
    context = DataContext(subcontext=dict(a=1,b=[2]))
    block = Block(code)
    # by default, clean shadow after execution:
    shadow = block.execute_impure(context)
    assert_equal(set(context.keys()), set(['a', 'b']))  # names unchanged
    assert_equal(context['b'], [2,3,4])  # mutable object was changed in context
    assert_equal(set(shadow.keys()), set(['x', 'z', 'a']))
    assert_equal(context['a'], 1)  # original mutable object does not change,
    assert_equal(shadow['a'], 99)  #  but the new object is in the shadow dict.
    # do not clean shadow after execution:
    shadow = block.execute_impure(context, clean_shadow=False)
    assert_equal(set(shadow.keys()), set(['x', 'z', 'a', '_x', 'os', 'ff']))


