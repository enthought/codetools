# Standard library imports
import unittest
import compiler

# Local imports
from codetools.blocks.api import unparse

class UnparseCompilerAstTestCase(unittest.TestCase):

    ##########################################################################
    # TestCase interface
    ##########################################################################

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    ##########################################################################
    # UnparseCompilerAstTestCase interface
    ##########################################################################

    ### Test methods  #######################################################
    def test_import(self):
        code = "from foo import bar, foo as baz"
        self._check_round_trip(code)

    def test_print(self):
        code = "print x"
        self._check_round_trip(code)

    def test_print_multitple(self):
        code = "print x, y, z"
        self._check_round_trip(code)

    def test_print_redirect(self):
        code = "print >> error, x"
        self._check_round_trip(code)

    def test_unary_minus(self):
        code = "a = -1"
        self._check_round_trip(code)

    def test_assign_attr(self):
        code = 'foo.bar = baz'
        self._check_round_trip(code)

    def test_assign_constant(self):
        code = "a = 1"
        self._check_round_trip(code)

    def test_multiple_assign_constant(self):
        code = "a, b = 1, 2"
        desired = "a, b = (1, 2)"
        self._check_round_trip(code, desired)

    def test_empty_tuple(self):
        code = "a = ()"
        self._check_round_trip(code)

    def test_float_precision(self):
        # We want 0.1 -> 0.1, not 0.10000000000001
        code = "0.1"
        self._check_round_trip(code)

    def test_function_call_without_return(self):
        code = "foo(a)"
        self._check_round_trip(code)

    def test_function_call_with_single_return(self):
        code = "b = foo(a)"
        self._check_round_trip(code)

    def test_function_call_with_multiple_return(self):
        code = "a, b = foo(a)"
        desired = "a, b = foo(a)"
        self._check_round_trip(code, desired)

    def test_function_call_with_multiple_inputs(self):
        code = "x = foo(a, b)"
        self._check_round_trip(code)

    def test_function_call_with_keyword_args(self):
        code = "x = foo(a, b=3)"
        self._check_round_trip(code)

    def test_function_call_with_star_args(self):
        code = "x = foo(*a)"
        self._check_round_trip(code)

    def test_function_call_with_dstar_args(self):
        code = "x = foo(**a)"
        self._check_round_trip(code)

    def test_function_call_with_arg_star_args_dstar_args(self):
        code = "x = foo(a, *b, **c)"
        self._check_round_trip(code)

    def test_function_definition(self):
        code = "def foo(a, b=3): \n" \
               "    return a"
        self._check_round_trip(code)

    def test_function_definition_multiple_returns(self):
        code = "def foo(a, b=3): \n" \
               "    return a, b"
        self._check_round_trip(code)

    def test_function_definition_with_decorator(self):
        code = "@testme\n" \
               "def foo(a, b=3): \n" \
               "    return a"
        self._check_round_trip(code)

    def test_function_definition_no_indent(self):
        code = "x = foo(a, b)\n" \
               "def bar(a, b): a = b+3; return a; \n" \
               "y = bar(a, b)"
        self._check_round_trip_func_no_indent(code)

    def test_compare(self):
        code = "x = a-1 > b"
        self._check_round_trip(code)

    def test_compare_multiple(self):
        code = "x = 1 > a > b"
        self._check_round_trip(code)

    def test_add(self):
        code = "x = a+1"
        self._check_round_trip(code)

    def test_sub(self):
        code = "x = a-1"
        self._check_round_trip(code)

    def test_mul(self):
        code = "x = a*1"
        self._check_round_trip(code)

    def test_div(self):
        code = "x = a/1"
        self._check_round_trip(code)

    def test_power(self):
        code = "x = a**1"
        self._check_round_trip(code)

    def test_expression(self):
        code = "x = x+(x+2)*2"
        self._check_round_trip(code)

    def test_expression2(self):
        code = "x = x**(2+x)*3+2"
        self._check_round_trip(code)

    def test_expression3(self):
        code = "x = x**2+3*x+3/2"
        self._check_round_trip(code)

    def test_getattr(self):
        code = "foo.bar.baz"
        self._check_round_trip(code)

    def test_if(self):
        code = "if True: \n" \
                   "    pass"
        self._check_round_trip(code)

    def test_if2(self):
        code = "if True: \n" \
                   "    \n" \
                   "    x = 4\n" \
                   "else: \n" \
                   "    \n" \
                   "    x = 5"
        self._check_round_trip(code)

    def test_if3(self):
        code = "if True: \n" \
                   "    pass\n\n" \
                   "elif False: \n" \
                   "    pass\n\n" \
                   "else: \n" \
                   "    pass"
        self._check_round_trip(code)

    def test_if4(self):
        """ tests nested if blocks."""
        # nested if blocks have an extra line
        code = "if True: \n" \
                   "    \n" \
                   "    if True: \n" \
                   "        pass"
        self._check_round_trip(code)

    def test_if5(self):
        """ tests if block nested in else block. """
        # nested if blocks have an extra line
        code = "if True: \n" \
                   "    pass\n\n" \
                   "else: \n" \
                   "    \n" \
                   "    if True: \n" \
                   "        pass"
        self._check_round_trip(code)

    def test_list(self):
        code = "[True]"
        self._check_round_trip(code)

    def test_list2(self):
        code = "[True, False]"
        self._check_round_trip(code)

    def test_list3(self):
        code = "[list()]"
        self._check_round_trip(code)

    def test_list4(self):
        code = "[1, 2, sin(3)]"
        self._check_round_trip(code)

    def test_subscript_with_int(self):
        code = "x = foo[0]"
        self._check_round_trip(code)

    def test_subscript_with_string(self):
        code = "x = foo['bar']"
        self._check_round_trip(code)

    def test_subscript_with_ellipses(self):
        code = "x = foo[...]"
        self._check_round_trip(code)

    def test_subscript_with_slice(self):
        code = "x = foo[1:2]"
        self._check_round_trip(code)

    def test_subscript_with_slice_no_lower(self):
        code = "x = foo[:1]"
        self._check_round_trip(code)

    def test_subscript_with_slice_no_upper(self):
        code = "x = foo[1:]"
        self._check_round_trip(code)

    def test_subscript_with_slice_no_lower_or_upper(self):
        code = "x = foo[:]"
        self._check_round_trip(code)

    def test_subscript_with_extended_slice(self):
        code = "x = foo[1:4:2]"
        self._check_round_trip(code)

    def test_subscript_with_extended_slice_no_lower(self):
        code = "x = foo[:4:2]"
        self._check_round_trip(code)

    def test_subscript_with_extended_slice_no_upper(self):
        code = "x = foo[1::2]"
        self._check_round_trip(code)

    def test_subscript_with_extended_slice_no_step(self):
        code = "x = foo[1:1:]"
        self._check_round_trip(code)

    def test_subscript_with_extended_slice_no_values(self):
        code = "x = foo[::]"
        self._check_round_trip(code)

    def test_subscript_with_multiple_dims(self):
        code = "x = foo[1,2]"
        self._check_round_trip(code)

    def test_subscript_with_multiple_dims_with_slices(self):
        code = "x = foo[1,::2]"
        self._check_round_trip(code)

    def test_short_program_with_doc_string(self):
        code = "'doc string'\n" \
               "from foo_mod import foo2 as foo, bar as bar2\n" \
               "c,d = foo(a,b=3)\n" \
               "k,l = foo2(a,b)\n" \
               "e = bar(c)\n" \
               "f = baz(d)\n" \
               "d = zi(e)\n"
        desired = "'doc string'\n" \
                  "from foo_mod import foo2 as foo, bar as bar2\n" \
                  "c, d = foo(a, b=3)\n" \
                  "k, l = foo2(a, b)\n" \
                  "e = bar(c)\n" \
                  "f = baz(d)\n" \
                  "d = zi(e)\n"

        self._check_round_trip(code, desired)

    def test_inline_string(self):
        code = "from foo_mod import foo2 as foo, bar as bar2\n" \
               "c, d = foo(a, b=3)\n" \
               "'inline string'\n" \
               "e = bar(c)\n" \

        self._check_round_trip(code)

    def test_bitand(self):
        code = "from numpy import arange\n"\
               "x = arange(0.0, 10.0, 1.0)\n"\
               "cond = (x > 4) & (x < 8)"
        self._check_round_trip(code)

    def test_bitor(self):
        code = "from numpy import arange\n"\
               "x = arange(0.0, 10.0, 1.0)\n"\
               "cond = (x > 4) | (x < 8)"
        self._check_round_trip(code)

    def test_augassign(self):
        # += check
        code = "c = 1\nc += 1"
        self._check_round_trip(code)

        # -= check
        code = "c = 1\nc -= 1"
        self._check_round_trip(code)

        # *= check
        code = "c = 1\nc *= 3"
        self._check_round_trip(code)

        # /= check
        code = "c = 2\nc /= 2"
        self._check_round_trip(code)

        # &= check
        code = "c = 1\nc &= 0"
        self._check_round_trip(code)

        # |= check
        code = "c = 0\nc |= 1"
        self._check_round_trip(code)

    def test_with(self):
        code = 'from __future__ import with_statement\n'\
               'with m: \n'\
               '    vp = 1.0'
        self._check_round_trip(code)

    def test_list_comp1(self):
        code = '[x for x in [1, 2, 3] if x != 2]'
        self._check_round_trip(code)

    def test_list_comp2(self):
        code = "[(x, y) for x in [1, 2, 3] if x != 2 for y in ['a', 'b']]"
        self._check_round_trip(code)

    def test_list_comp3(self):
        code = "[(x, y) for x in [1, 2, 3] if x != 2 if x > 0 for y in ['a', 'b']]"
        self._check_round_trip(code)

    def test_gen_expr1(self):
        code = '(x for x in [1, 2, 3] if x != 2)'
        self._check_round_trip(code)

    def test_gen_expr2(self):
        code = "((x, y) for x in [1, 2, 3] if x != 2 for y in ['a', 'b'])"
        self._check_round_trip(code)

    def test_gen_expr3(self):
        code = "((x, y) for x in [1, 2, 3] if x != 2 if x > 0 for y in ['a', 'b'])"
        self._check_round_trip(code)

    def test_gen_expr4(self):
        code = 'all((x for x in [1, 2, 3] if x != 2))'
        self._check_round_trip(code)

    ### private utility methods  #############################################

    def _check_round_trip(self, code, desired=None):
        """ Check the roundtripped code against a desired result.

            if desired=None (default), then check it against the input code.
        """
        if desired is None:
            desired = code
        ast = compiler.parse(code,'exec')
        actual = unparse(ast)
        self.assertEqual(desired.strip(), actual.strip())

    def _check_round_trip_func_no_indent(self, code, desired=None):
        """ Check the roundtripped code against a desired result. Function
            definitions will be on a single line.

            if desired=None (default), then check it against the input code.
        """
        if desired is None:
            desired = code
        ast = compiler.parse(code,'exec')
        actual = unparse(ast, True)
        self.assertEqual(desired.strip(), actual.strip())


if __name__ == '__main__':
    unittest.main()
