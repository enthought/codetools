import os
from numpy.testing import assert_equal, assert_
from codetools.blocks.namespace_tools import *

def test_Namespace_class():
    ns = Namespace({'a':1, 'b':2})
    assert_equal(ns.a, 1)
    assert_equal(ns.b, 2)

def test_namespace_decorator():
    # Test simple cases
    @namespace
    def foo(x,y=1):
        pass

    # assignment in function call, with and without defaults:
    results = foo(1)
    assert_equal(results.x, 1)
    assert_equal(results.y, 1)

    results = foo(1,2)
    assert_equal(results.x, 1)
    assert_equal(results.y, 2)

    results = foo(1,y=2)
    assert_equal(results.x, 1)
    assert_equal(results.y, 2)

    # iteration:
    assert_equal(sorted(item for item in results if item[0][0] != "_"),
                 [('x',1),('y',2)])

    # index notation:
    assert_equal(results['x'], 1)
    results['z'] = 3
    assert_equal(results.z, 3)

    # assignment in function body:
    @namespace
    def bar(y=30):
        x = 3
    results = bar()
    assert_equal(results.x, 3)
    assert_equal(results.y, 30)

def test_decorated_has_no_keywords():
    @namespace
    def foo(x,y):
        z = 3
    results = foo(1,2)
    assert_equal(results.x, 1)
    assert_equal(results.y, 2)
    assert_equal(results.z, 3)

    @namespace
    def bar():
        z = 3
    res2 = bar()
    assert_equal(res2.z, 3)


def test_namespace_from_keywords():
    numbers = namespace_from_keywords( little=1, medium=3, big=99)
    assert_equal(numbers.little, 1)
    assert_equal(numbers.medium, 3)
    assert_equal(numbers.big, 99)


code_to_exec = """
@namespace
def f(x=1):
    y = a
ns = f()
"""

def test_namespace_in_execfile():
    tempfile = ".temp"
    with file(tempfile, 'w') as f:
        f.write(code_to_exec)
    dic = {'a':2, 'namespace':namespace}
    execfile(tempfile, dic)
    assert_equal(set(dic.keys()), set(['a', '__builtins__', 'namespace',
                                       'f', 'ns']))
    ns = dic['ns']
    assert_equal(ns.x, 1)
    assert_equal(ns.y, 2)
    os.remove(tempfile)

def test_namespace_in_exec():
    # Verify that namespace decorator does *NOT* work in exec'd code.
    dic = {'a':2, 'namespace':namespace}
    exec code_to_exec in dic
    assert_equal(set(dic.keys()), set(['a', '__builtins__', 'namespace',
                                       'f', 'ns']))
    ns = dic['ns']
    assert_('x' in dir(ns))
    assert_('y' not in dir(ns))
    assert_equal(ns.x, 1)
