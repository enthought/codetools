# Standard library imports
import unittest

# Geo library imports
from enthought.contexts.api import MultiContext, DataContext
from enthought.contexts.shell.global_and_local_interpreter import \
                                        GlobalAndLocalInterpreter

class GlobalAndLocalInterpreterTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.globals = {}
        self.locals = MultiContext(self.globals)
        self.interpreter = GlobalAndLocalInterpreter(locals=self.locals,
                                                     globals=self.globals)

        # Name of local variable name to use in expressions
        self.input_name = 'vp'

        # Value to use in expressions.
        self.local_input = 1
        self.global_input = 1

    def tearDown(self):
        unittest.TestCase.tearDown(self)


    def test_default_construction(self):
        """ Can we create a default interpreter?
        """
        interpreter = GlobalAndLocalInterpreter()

    def test_set_item_local(self):
        """ Can we set a value to the local dictionary?
        """
        # vp=1
        expr = "%s=%s" % (self.input_name, self.local_input)
        self.interpreter.push(expr)
        self.assertEqual(self.locals[self.input_name], self.local_input)

    def test_del_item_local(self):
        """ Can we we delete an item from locals?
        """

        # vp=1
        expr = "%s=%s" % (self.input_name, self.local_input)
        self.interpreter.push(expr)
        # del vp
        expr = "del %s" % self.input_name
        self.interpreter.push(expr)

        self.assertFalse(self.locals.has_key(self.input_name))

    def test_del_item_global_with_global_statement(self):
        """ Can we delete a global variable if declared global?
        """
        self.globals[self.input_name] = self.global_input
        # assert(vp==1)
        expr = "assert(%s==%s)" % (self.input_name, self.global_input)
        self.interpreter.push(expr)
        # global vpl; del vp;
        expr = "global %s; del %s" % (self.input_name, self.input_name)
        self.interpreter.push(expr)

        self.assertFalse(self.globals.has_key(self.input_name))

    def test_del_item_global(self):
        """ Can we delete a global variable even if it isn't declared global?
        """
        self.globals[self.input_name] = self.global_input
        self.assertTrue(self.globals.has_key(self.input_name))        
        # assert(vp==1)
        expr = "assert(%s==%s)" % (self.input_name, self.global_input)
        self.interpreter.push(expr)
        # del vp;
        expr = "del %s" % self.input_name
        self.interpreter.push(expr)

        self.assertFalse(self.locals.has_key(self.input_name))
        self.assertFalse(self.globals.has_key(self.input_name))

    def test_wildcard_style_imports(self):
        """ Can we use 'from xyz import *'?
        """
        self.interpreter.push("from sys import *")
        self.assertTrue(self.globals.has_key('exc_info'))

    def test_list_comprehension(self):
        """ Can we run a list comprehension in the interpreter?
        """
        self.interpreter.push("val = [x for x in [1,2,3]]")


if __name__ == '__main__':
    unittest.main()

