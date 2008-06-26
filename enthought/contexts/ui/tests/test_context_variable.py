from nose.tools import assert_raises

from enthought.traits.api import TraitError, Undefined

from enthought.contexts.ui.context_variable import ContextVariable


def test_context_variable_getitem():
    """ Does the ContextVariable respond to indexing correctly for sorting?
    """
    cv = ContextVariable(name='the_name', value=1, type='foo')
    assert cv[0] == 'the_name'
    assert cv[1] is None
    assert cv[2] is None

def test_int_context_variable_editable():
    """ Does an int ContextVariable choose its editable flag correctly?
    """
    cv = ContextVariable(name='int', value=1, type='int')
    assert not cv.editable
    assert cv.value == 1

def test_float_context_variable_editable():
    """ Does a float ContextVariable choose its editable flag correctly?
    """
    cv = ContextVariable(name='float', value=1.5, type='float')
    assert not cv.editable
    assert cv.value == 1.5

def test_str_context_variable_editable():
    """ Does a str ContextVariable choose its editable flag correctly?
    """
    cv = ContextVariable(name='str', value='foo', type='str')
    assert not cv.editable
    assert cv.value == 'foo'

def test_uni_context_variable_editable():
    """ Does a unicode ContextVariable choose its editable flag correctly?
    """
    cv = ContextVariable(name='unicode', value=u'foo', type='unicode')
    assert not cv.editable
    assert cv.value == u'foo'

def test_other_context_variable_editable():
    """ Does a generic ContextVariable choose its editable flag correctly?
    """
    cv = ContextVariable(name='object', value=object(), type='object')
    assert cv.editable
    assert cv.value is not None

def test_value_undefined_error():
    """ Does assigned Undefined to .value raise a TraitError?
    """
    cv = ContextVariable()
    assert_raises(TraitError, cv.set, value=Undefined)

