from unittest import TestCase

from codetools.execution.formula_executing_context import *
from codetools.contexts.data_context import DataContext
from traits.util.refresh import refresh


class FormulaExecutingContextTest(TestCase):

    def test_simple_execution_manager(self):
        code = """b=a*10
"""
        e = FormulaExecutingContext()
        e.data_context = DataContext()
        e.data_context['a'] = 5
        e.external_code=code
        assert(e.data_context['b'] == 50)
        e.external_code = """c=a*20
"""
        assert(e.data_context['c'] == 100)
        e['f'] = '=a*100'
        assert(e.data_context['f'] == 500)
        assert(e['f'] == '500=a*100')
