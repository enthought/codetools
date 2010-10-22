from numpy.testing import assert_equal

from enthought.contexts.api import DataContext, AdaptedDataContext, NameAdapter


def test_name_adapter_get():

    obj1 = object()
    obj2 = object()
    obj3 = object()

    subcx = DataContext(subcontext=dict(a1=obj1, a2=obj2))

    name_map1 = {
        'b1':'a1',
        'b2':'a2',
       }
    name_map2 = {
        'c1':'b1',
        'c2':'b2',
       }

    name_adapter1 = NameAdapter(map=name_map1)
    name_adapter2 = NameAdapter(map=name_map2)
    context = AdaptedDataContext(subcontext=subcx)

    # Note that the adapters are pushed in the order that the
    # names must be mapped: first c->b, then b->a. (FIFO, not LIFO)
    context.push_adapter(name_adapter2)
    context.push_adapter(name_adapter1)

    # getitem
    assert_equal( context['a1'], obj1)
    assert_equal( context['b1'], obj1)
    assert_equal( context['c1'], obj1)

    assert_equal( context['a2'], obj2)
    assert_equal( context['b2'], obj2)
    assert_equal( context['c2'], obj2)

    # setitem
    context['c2'] = obj3
    assert_equal( context['c2'], obj3)
    assert_equal( context['b2'], obj3)
    assert_equal( context['a2'], obj3)

    assert_equal( context['a1'], obj1)
    assert_equal( context['b1'], obj1)
    assert_equal( context['c1'], obj1)

