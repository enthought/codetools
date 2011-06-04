from numpy.testing import assert_equal, assert_

from traits.api import Dict
from codetools.contexts.api import (DataContext, AdaptedDataContext,
                                    NameAdapter, IterableAdaptedDataContext,
                                    UnitConversionAdapter)


def test_name_adapter_get_set():

    obj1 = object()
    obj2 = object()
    obj3 = object()

    subcx = DataContext(subcontext=dict(a1=obj1, a2=obj2))

    name_map1 = {
        'b1':'a1',
        'b2':'a2',
        'b3':'a3'  # nonexistent
       }
    name_map2 = {
        'c1':'b1',
        'c2':'b2',
        'c3':'b3', # eventually nonexistent
       }

    name_adapter1 = NameAdapter(map=name_map1)
    name_adapter2 = NameAdapter(map=name_map2)
    # unit adapter won't do anything, just ensure doesn't block flow or choke.
    unit_adapter = UnitConversionAdapter()
    context = AdaptedDataContext(subcontext=subcx)

    # Note that the adapters are pushed with those closest to the context first.
    # b->a, then c->b. (FIFO, not LIFO)
    context.push_adapter(name_adapter1)
    context.push_adapter(unit_adapter)
    context.push_adapter(name_adapter2)

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

    # IterableAdaptedDataContext
    context2 = IterableAdaptedDataContext(subcontext=subcx)
    context2.push_adapter(name_adapter1)
    context2.push_adapter(unit_adapter)
    context2.push_adapter(name_adapter2)

    assert_equal(set(context2.keys()), set('a1 a2 b1 b2 c1 c2'.split()))
    assert_equal(set([k for k in context2]), set(context2.keys()))
    for key in context2:
        assert_(key in context2)
    assert_('b3' not in context2)
    assert_('c3' not in context2)



def test_stacked_hybrid_adapters():
    """ Test the stacked application of multiple adapters which adapt both
    names and values. This tests a bug in AdapterManagerMixin which applied
    name adapters in backwards order. Without value transformation as well as
    name mapping, it's not as obvious what the correct order of name
    adaptation should be. But the essence is that the first adapter applied is
    the one closest to the underlying context.
    """
    # Converts freezing & boiling temps of water between F, C, and approx K,
    # to test adapters whose composition is not commutative.
    FF = 32.
    BF = 212.
    FC = 0.
    BC = 100.
    FK = 273.
    BK = 373.

    # These adapters are named with the units closer to context on the left,
    # and units closer to the user on the right. Context is F, user is C or K.
    # Note that any changes made by adapt_getitem, to name, are only for the
    # use of other adapters -- such name changes do not otherwise affect the
    # value ultimately returned by the original top level __getitem__.

    class AdaptCtoK(NameAdapter):
        map = Dict({'frK':'frC', 'boK':'boC'})

        def adapt_getitem(self, context, name, value):
            if name[-1] == 'C':
                return name[:-1]+'K', value+FK
            else:
                assert_(False, 'AdaptCtoK called unexpectedly on %s' % name)


    class AdaptFtoC(NameAdapter):
        map = Dict({'frC':'frF', 'boC':'boF'})

        def adapt_getitem(self, context, name, value):
            if name[-1] == 'F':
                return name[:-1]+'C', (value-FF)*(BC-FC)/(BF-FF)
            else:
                assert_(False, 'AdaptFtoC called unexpectedly on %s' % name)


    farenheit_context = DataContext(subcontext=dict(frF=FF, boF=BF))

    # no adapter
    context = AdaptedDataContext(subcontext=farenheit_context)
    assert_equal(context['frF'], FF)
    assert_equal(context['boF'], BF)

    # one adapter: to Celsius
    # Note that the data are adapted to Celsius even if we retrieve them
    # with a Farenheit name, because getitem adapters are not told the
    # original retrieval key.
    context.push_adapter(AdaptFtoC())
    assert_equal(context['frF'], FC)
    assert_equal(context['frC'], FC)
    assert_equal(context['boF'], BC)
    assert_equal(context['boC'], BC)

    # two adapters: to Kelvin (no matter which name is used to retrieve).
    # unit adapter won't do anything, just ensure doesn't block flow or choke.
    context.push_adapter(UnitConversionAdapter())
    context.push_adapter(AdaptCtoK())
    assert_equal(context['frF'], FK)
    assert_equal(context['frC'], FK)
    assert_equal(context['frK'], FK)
    assert_equal(context['boF'], BK)
    assert_equal(context['boC'], BK)
    assert_equal(context['boK'], BK)


