import unittest

from enthought.contexts.data_context import DataContext
from enthought.contexts.multi_context import MultiContext


class Events2TestCase(unittest.TestCase):
    """ Test events with the new contexts.
    """
    
    def setUp(self):
        self.event_count = 0
        self.last_event = None
        
    def event_listener(self, event):
        self.event_count += 1
        self.last_event = event
            
    def test_assign_value(self):
        context = DataContext()
        context.on_trait_change(self.event_listener, 'items_modified')
        context['a'] = 'foo'
        
        self.assertEqual(self.event_count, 1)
        self.assertEqual(self.last_event.added, ['a'])
        self.assertEqual(self.last_event.modified, [])
        self.assertEqual(self.last_event.removed, [])

    def test_change_value(self):
        context = DataContext()
        context.on_trait_change(self.event_listener, 'items_modified')
        context['a'] = 'foo'
        context['a'] = 'foo2'
        
        self.assertEqual(self.event_count, 2)
        self.assertEqual(self.last_event.added, [])
        self.assertEqual(self.last_event.modified, ['a'])
        self.assertEqual(self.last_event.removed, [])

    def test_defer_add_event(self):
        context = DataContext()
        context.on_trait_change(self.event_listener, 'items_modified')
        context.defer_events = True
        context['a'] = 'foo'
        context.defer_events = False
        
        self.assertEqual(self.event_count, 1)
        self.assertEqual(self.last_event.added, ['a'])
        self.assertEqual(self.last_event.modified, [])
        self.assertEqual(self.last_event.removed, [])

    def test_defer_multiple_events(self):
        context = DataContext()
        context.on_trait_change(self.event_listener, 'items_modified')
        context.defer_events = True
        self.assertEqual(self.event_count, 0)
        context['a'] = 'foo'
        self.assertEqual(self.event_count, 0)
        context['a'] = 'foo2'
        self.assertEqual(self.event_count, 0)
        context['b'] = 'bar'
        self.assertEqual(self.event_count, 0)
        context.defer_events = False

        # the modified will be empty, because it was also added
        self.assertEqual(self.event_count, 1)
        self.assertEqual(set(self.last_event.added), set(['a', 'b']))
        self.assertEqual(self.last_event.modified, [])
        self.assertEqual(self.last_event.removed, [])

    def test_delete_after_add(self):
        context = DataContext()
        context.on_trait_change(self.event_listener, 'items_modified')
        self.assertEqual(self.event_count, 0)
        context.defer_events = True
        self.assertEqual(self.event_count, 0)
        context['a'] = 'foo'
        self.assertEqual(self.event_count, 0)
        del context['a']
        self.assertEqual(self.event_count, 0)
        context.defer_events = False

        self.assertEqual(self.event_count, 0)

    def test_delete_after_modify(self):
        context = DataContext()
        context['a'] = 'foo'
        context.on_trait_change(self.event_listener, 'items_modified')
        self.assertEqual(self.event_count, 0)
        context.defer_events = True
        self.assertEqual(self.event_count, 0)
        context['a'] = 'foo2'
        self.assertEqual(self.event_count, 0)
        del context['a']
        self.assertEqual(self.event_count, 0)
        context.defer_events = False

        self.assertEqual(self.event_count, 1)
        self.assertEqual(self.last_event.added, [])
        self.assertEqual(self.last_event.modified, [])
        self.assertEqual(self.last_event.removed, ['a'])
        
    def test_block_events(self):
        import numpy
        from enthought.blocks.api import Block
        
        context = DataContext(name="data")
        context.on_trait_change(self.event_listener, 'items_modified')
        context.defer_events = True
        context['a'] = 4
        context['b'] = numpy.array((1,2,3))
        context.defer_events = False
        
        self.assertEqual(self.event_count, 1)
        
        multi_context = MultiContext(context, name="multi")
        multi_context.on_trait_change(self.event_listener, 'items_modified')
        
        block = Block("c = a * b")
        block.execute(multi_context)

        # we expect one event from data context, one from multi context
        self.assertEqual(self.event_count, 3)
        
