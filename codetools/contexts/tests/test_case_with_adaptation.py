import unittest

# ETS imports
from traits.adaptation.api import (
    AdaptationManager,
    get_global_adaptation_manager,
    set_global_adaptation_manager,
)

# Geo library imports
from codetools.contexts.data_context import register_i_context_adapter_offers
from codetools.contexts.i_context import (
    register_dict_to_context_adapter_offers,
)


class TestCaseWithAdaptation(unittest.TestCase):
    """
    A subclass of unittest.TestCase whose setUp creates a fresh
    global adaptation manager and registers codetools adaptation offers
    in that manager.
    """
    def setUp(self):
        self._old_adaptation_manager = get_global_adaptation_manager()
        adaptation_manager = AdaptationManager()
        set_global_adaptation_manager(adaptation_manager)

        register_i_context_adapter_offers(adaptation_manager)
        register_dict_to_context_adapter_offers(adaptation_manager)

    def tearDown(self):
        set_global_adaptation_manager(self._old_adaptation_manager)
