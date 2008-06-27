from enthought.block_canvas.context.api import DataContext
from enthought.block_canvas.execution.api import ExpressionContext

import unittest
class ExpressionContextTest(unittest.TestCase):
    def test_eval(self):
        """Test most straightforward evaluation functionality"""
        d = DataContext()
        d['a'] = 10
        d['b'] = 20
        ec = ExpressionContext(d)
        self.assertEqual(200, ec['a*b'])

    def test_events(self):
        self.last_event = None
        self.event_count = 0
        d = DataContext()
        d['a'] = 10
        d['b'] = 20
        ec = ExpressionContext(d)
        ec['a*b']
        ec.on_trait_change(self._event_handler, 'items_modified')
        ec['a'] = 30
        assert 'a' in self.last_event.modified
        assert 'a*b' in self.last_event.modified

    def _event_handler(self, event):
        self.event_count += 1
        self.last_event = event
                         
                         
    
