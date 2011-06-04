import unittest

from codetools.contexts.adapter.adapter_manager_mixin import AdapterManagerMixin
from codetools.contexts.adapter.unit_conversion_adapter import UnitConversionAdapter


class AdapterManagerMixinTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.manager = AdapterManagerMixin()
        self.adapter = UnitConversionAdapter()
    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_push_pop(self):
        self.manager.push_adapter(self.adapter)
        popped_adapter = self.manager.pop_adapter()
        self.assertEqual(self.adapter, popped_adapter)

if __name__ == '__main__':
    unittest.main()
