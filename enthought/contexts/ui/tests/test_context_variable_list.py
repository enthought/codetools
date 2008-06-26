from nose.tools import assert_equal
import numpy as np
from numpy.testing import assert_array_equal

from enthought.contexts.api import DataContext
from enthought.contexts.ui.context_variable import (ContextVariable,
    ContextVariableList)


def gen_context():
    """ Create a test context.
    """
    dc = DataContext()
    dc['foo_int'] = 1
    dc['foo_float'] = 1.5
    dc['foo_array'] = np.arange(10)
    dc['foo_str'] = 'a string'
    dc['bar_int'] = 2
    dc['bar_float'] = 2.5

    return dc

def test_init():
    dc = gen_context()
    cvl = ContextVariableList(context = dc)
    yield assert_equal, cvl.search_term, ''
    names = set(dc.keys())
    yield assert_equal, set([v.name for v in cvl.variables]), names
    yield assert_equal, set([v.name for v in cvl.search_results]), names
    for cv in cvl.variables:
        if isinstance(cv.value, np.ndarray):
            yield assert_array_equal, cv.value, dc[cv.name]
        else:
            yield assert_equal, cv.value, dc[cv.name]

def test_subcontext():
    dc = gen_context()
    dc['subcontext'] = dict(baz_int=3, baz_float=3.5)
    cvl = ContextVariableList(context=dc)
    names = set(dc.keys())
    names.add("subcontext['baz_int']")
    names.add("subcontext['baz_float']")
    names.remove('subcontext')
    assert_equal(set([v.name for v in cvl.variables]), names)
    assert_equal(set([v.name for v in cvl.search_results]), names)

def test_search():
    dc = gen_context()
    cvl = ContextVariableList(context=dc)
    cvl.search_term = 'bar'
    names = set(['bar_int', 'bar_float'])
    yield assert_equal, set([v.name for v in cvl.search_results]), names

    cvl.search_term = '*int'
    names = set(['foo_int', 'bar_int'])
    yield assert_equal, set([v.name for v in cvl.search_results]), names

    cvl.search_term = '*ar_*'
    names = set(['bar_int', 'bar_float'])
    yield assert_equal, set([v.name for v in cvl.search_results]), names

    cvl.search_term = 'foo,bar'
    names = set(dc.keys())
    yield assert_equal, set([v.name for v in cvl.search_results]), names

def test_row_value_changed():
    dc = gen_context()
    cvl = ContextVariableList(context=dc)
    row = cvl.search_results[0]   
    assert dc[row.name] != 100
    row.value = 100
    assert dc[row.name] == 100

def test_add_row():
    dc = gen_context()
    cvl = ContextVariableList(context=dc)
    cvl.search_results.append(ContextVariable(name='new', value='variable'))
    assert dc['new'] == 'variable'

def test_delete_row():
    dc = gen_context()
    cvl = ContextVariableList(context=dc)
    last_row = cvl.search_results[-1]
    del cvl.search_results[-1]
    assert last_row.name not in dc

