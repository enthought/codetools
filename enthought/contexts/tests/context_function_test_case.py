import unittest
import math

import numpy

from enthought.contexts.context_function import context_function

c = 5.0

def basic(a, b):
    if a < 0:
        return b
    else:
        d = a*b+c
    return d

def data_structures(a, b):
    if isinstance(a, list):
        a = [i*2 for i in a]
    b[12] = 17
    return a, b

def star_args(a, *args):
    d = []
    for arg in args:
        d.append(arg*a+c)
    return d

def kw_args(a, **kwargs):
    d = {}
    for key, value in kwargs.items():
        d[key] = value*a+c
    return d

def star_and_kw_args(a, *args, **kwargs):
    d = []; e = {}
    for arg in args:
        d.append(arg*a+c)
    for key, value in kwargs.items():
        e[key] = value*a+c
    return d, e

def math_func(x):
    a = 2
    return a*math.sin(x) + math.cos(x)

class ContextFunctionTestCase(unittest.TestCase):
    
    def test_basic_functionality(self):
        c = 5.0
        context_basic = context_function(basic, dict)
        self.assertEqual(basic(1, 2), context_basic(1, 2))
        self.assertEqual(basic(-1, 2), context_basic(-1, 2))
        c = 10.0
        self.assertEqual(basic(1, 2), context_basic(1, 2))
        self.assertEqual(basic(-1, 2), context_basic(-1, 2))
    
    def test_star_args(self):
        c = 5.0
        context_basic = context_function(basic, dict)
        self.assertEqual(basic(*(1,2)), context_basic(*(1,2)))
        context_star_args = context_function(star_args, dict)
        a=2
        self.assertEqual(star_args(a, 2, 3, 4, 5),
                         context_star_args(a, 2, 3, 4, 5))
        self.assertEqual(star_args(a, 2, *(3, 4, 5)),
                         context_star_args(a, 2, *(3, 4, 5)))
        self.assertEqual(star_args(*(a, 2, 3, 4, 5)),
                         context_star_args(*(a, 2, 3, 4, 5)))
    
    def test_kw_args(self):
        c = 5.0
        context_basic = context_function(basic, dict)
        self.assertEqual(basic(a=1, b=2), context_basic(a=1, b=2))
        self.assertEqual(basic(1, b=2), context_basic(1, b=2))
        context_kw_args = context_function(kw_args, dict)
        a=2
        self.assertEqual(kw_args(a, b=2, c=3, d=4, e=5),
                         context_kw_args(a, b=2, c=3, d=4, e=5))
        self.assertEqual(kw_args(a=a, b=2, c=3, d=4, e=5),
                         context_kw_args(a=a, b=2, c=3, d=4, e=5))
        kwarg = dict(a=a, b=2, c=3, d=4, e=5)
        self.assertEqual(kw_args(**kwarg),
                         context_kw_args(**kwarg))
    
    def test_star_and_kw_args(self):
        c = 5.0
        context_basic = context_function(basic, dict)
        kwarg = dict(b=2)
        self.assertEqual(basic(b=2, *(1,)), context_basic(b=2, *(1,)))
        self.assertEqual(basic(*(1,), **kwarg), context_basic(*(1,), **kwarg))
        context_star_and_kw_args = context_function(star_and_kw_args, dict)
        a=2
        self.assertEqual(star_and_kw_args(a, 2, 3, d=4, e=5),
                         context_star_and_kw_args(a, 2, 3, d=4, e=5))
        self.assertEqual(star_and_kw_args(a, b=2, c=3, d=4, e=5),
                         context_star_and_kw_args(a, b=2, c=3, d=4, e=5))
        self.assertEqual(star_and_kw_args(a=a, b=2, c=3, d=4, e=5),
                         context_star_and_kw_args(a=a, b=2, c=3, d=4, e=5))
        self.assertEqual(star_and_kw_args(a, 2, 3, 4, 5),
                         context_star_and_kw_args(a, 2, 3, 4, 5))
        self.assertEqual(star_and_kw_args(a, 2, *(3, 4, 5)),
                         context_star_and_kw_args(a, 2, *(3, 4, 5)))
        self.assertEqual(star_and_kw_args(*(a, 2, 3, 4, 5)),
                         context_star_and_kw_args(*(a, 2, 3, 4, 5)))
        kwarg = dict(a=a, b=2, c=3, d=4, e=5)
        self.assertEqual(star_and_kw_args(**kwarg),
                         context_star_and_kw_args(**kwarg))
        arg = (a, 2, 3); kwarg = dict(d=4, e=5)
        self.assertEqual(star_and_kw_args(*arg, **kwarg),
                         context_star_and_kw_args(*arg, **kwarg))
        arg = (2, 3); kwarg = dict(d=4, e=5)
        self.assertEqual(star_and_kw_args(a, *arg, **kwarg),
                         context_star_and_kw_args(a, *arg, **kwarg))
    
    def test_data_structures(self):
        context_data = context_function(data_structures, dict)
        a = [2, 3, 'a']; b = {12: 7, 'a': 3, '4': 56}
        self.assertEqual(data_structures(a, b), context_data(a, b))
    
    def test_global_replacement(self):
        def numpy_math_factory():
            return {'math': numpy}
        numpy_func = context_function(math_func, numpy_math_factory)
        assert numpy.allclose(numpy_func(numpy.array([0.0, 0.25, 0.5])*numpy.pi),
                               numpy.array([1.0, 2.1213203435596424, 2.0]))