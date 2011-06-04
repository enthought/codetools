""" This example demonstrates how we can use a context function, to replace
a global reference with another object in the internals of a function.

There are two parts of this example:
  1. a "poor-man's vectorize" which shows how you can replace math functions
     with the equivalent numpy ones (full generality is an exercise for the
     reader).
  2. a "poor-man's closure" where a variable accumulates a value over several
     execution cycles of a function.
"""

from codetools.contexts.api import context_function, local_context

#############################################################################
# Example 1
#############################################################################

import math
def f(x):
    """This function knows nothing of numpy"""
    return 2*math.sin(x) + math.cos(x)


import numpy
def numpy_math_context():
    """This function returns a context where 'math' is a reference to numpy."""
    return {'math': numpy}

# this essentially vectorizes the function
f = context_function(f, numpy_math_context)

# so that this works
print f(numpy.array([0, 0.5, 1])*numpy.pi)


#############################################################################
# Example 2
#############################################################################

accumulation_dict = {'total': 0}

def accumulator_factory():
    """Return the same dictionary on every function call"""
    return accumulation_dict

@local_context(accumulator_factory)
def accumulator(value):
    """Accumulate total in accumulation_dict"""
    total += value

for i in range(10):
    accumulator(i)
    print accumulation_dict['total']
