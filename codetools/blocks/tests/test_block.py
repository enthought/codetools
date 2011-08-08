"""Tests for the Block class."""

from codetools.blocks.api import Block
from codetools.contexts.api import DataContext
import unittest

class Test(unittest.TestCase):
    
    def test_basic_01(self):
        """Test basic use of a Block."""
        code = 'x = 100\ny = x + 1'
        b = Block(code)
        self.assertEqual(b.inputs, set([]))
        self.assertEqual(b.outputs, set(['x','y']))
    
        names = dict()
        b.execute(names)
        self.assertEqual(sorted(names), ['x', 'y'])
        self.assertEqual(names['x'], 100)
        self.assertEqual(names['y'], 101)
    
    def test_basic_02(self):
        """Another test of the basic use of a Block."""
        code = 'y = x + 1'
        b = Block(code)
        self.assertEqual(b.inputs, set(['x']))
        self.assertEqual(b.outputs, set(['y']))
    
        names = dict(x=100)
        b.execute(names)
        self.assertEqual(sorted(names), ['x', 'y'])
        self.assertEqual(names['x'], 100)
        self.assertEqual(names['y'], 101)
    
    def test_restrict_inputs(self):
        """Test a basic use of the restrict(inputs=(...)) method."""
        code = 'x = a + b\ny = b - c\nz = c**2'
        b = Block(code)
        self.assertEqual(b.inputs, set(['a','b','c']))
        self.assertEqual(b.outputs, set(['x','y','z']))
    
        br = b.restrict(inputs=('a',))
        names = dict(a=100, b=200)
        br.execute(names)
        self.assertEqual(sorted(names), ['a', 'b', 'x'])
        self.assertEqual(names['a'], 100)
        self.assertEqual(names['b'], 200)
        self.assertEqual(names['x'], 300)
    
    def test_restrict_outputs(self):
        """Test a basic use of the restrict(outputs=(...)) method."""
        code = 'x = a + b\ny = b - c\nz = c**2'
        b = Block(code)
    
        br = b.restrict(outputs=('z',))
        names = dict(c=5)
        br.execute(names)
        self.assertEqual(sorted(names), ['c', 'z'])
        self.assertEqual(names['c'], 5)
        self.assertEqual(names['z'], 25)
    
    def test_restricted_empty_inputs(self):
        """Check that restrict(inputs=()) raises a ValueError."""
        code = 'x = a + b\ny = b - c\nz = c**2'
        b = Block(code)
        with self.assertRaises(ValueError):
            b.restrict(inputs=())
    
    def test_restricted_empty_outputs(self):
        """Check that restrict(outputs=()) raises a ValueError."""
        code = 'x = a + b\ny = b - c\nz = c**2'
        b = Block(code)
        with self.assertRaises(ValueError):
            b.restrict(outputs=())
    
    
    @unittest.expectedFailure
    def test_impure_execute(self):
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
        self.assertEqual(set(context.keys()), set(['a', 'b']))  # names unchanged
        self.assertEqual(context['b'], [2,3,4])  # mutable object was changed in context
        self.assertEqual(set(shadow.keys()), set(['x', 'z', 'a']))
        self.assertEqual(context['a'], 1)  # original mutable object does not change,
        self.assertEqual(shadow['a'], 99)  #  but the new object is in the shadow dict.
        # do not clean shadow after execution:
        shadow = block.execute_impure(context, clean_shadow=False)
        self.assertEqual(set(shadow.keys()), set(['x', 'z', 'a', '_x', 'os', 'ff']))
    

