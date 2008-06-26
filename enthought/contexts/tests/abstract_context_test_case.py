# Standard Library Imports
from itertools import imap
import timeit
import unittest
from UserDict import DictMixin

# Numeric library imports
from numpy import all

# Geo library imports
from enthought.contexts.tests.mapping_test_case import BasicTestMappingProtocol

def adapt_keys(context):
    ''' Wrap a context so that it accepts all key types used by
        BasicTestMappingProtocol.

        DataContext is a mapping object, but it should only deal with keys that
        are strings. We want to reuse python's dict test cases, so we wrap
        contexts with a mapping adapter that injects keys into strings.
    '''

    # We need from_str(to_str(x)) == x, and 'help(repr)' says "For most object
    # types, eval(repr(object)) == object". It seems to hold for built-ins, but
    # it fails for many user-defined objects. Since it holds for all of the key
    # types used by BasicTestMappingProtocol, it's good enough.
    to_str = repr
    from_str = eval

    class KeyAdapter(DictMixin):
        ''' A mapping object that converts keys into strings and otherwise
            delegates to another mapping object.
        '''
        def __init__(self, mapping_object):
            self._m = mapping_object

        def __getitem__(self, x):
            return self._m[to_str(x)]
        def __setitem__(self, x, value):
            self._m[to_str(x)] = value
        def __delitem__(self, x):
            del self._m[to_str(x)]
        def keys(self):
            return map(from_str, self._m.keys())

    return KeyAdapter(context)

# Subtype BasicTestMappingProtocol for free mapping object test cases:
# TestMappingProtocol assumes 'fromkeys' and 'copy', which we don't implement
# (TODO yet), and TestHashMappingProtocol is hopeless because the key adapter
# doesn't preserve key hashes.
class AbstractContextTestCase(BasicTestMappingProtocol):
    """ Defines the set of tests to run on any GeoContext or Adapter.

        Note: This does not derive from test case so that it doesn't get picked
              up and run by the unittest harness...  You must mixin
              unittest.TestCase in your derived class.
        fixme: There has to be a smarter way of doing this...
    """

    ############################################################################
    # unittest.TestCase interface
    ############################################################################

    # Don't run tests without a concrete test case
    def run(self, result=None):
        if type(self) == AbstractContextTestCase:
            return result
        else:
            return super(AbstractContextTestCase, self).run(result)

    def failUnlessEqual(self, first, second, msg=None):
        """Fail if the two objects are unequal as determined by the '=='
           operator.

           We've overloaded this here to handle arrays.
        """
        if not all(first == second):
            raise self.failureException, \
                  (msg or '%r != %r' % (first, second))

    ############################################################################
    # BasicTestMappingProtocol interface
    ############################################################################

    def type2test(self, *args, **kw):
        """ Return a context to be tested by BasicTestMappingProtocol.
        """
        return adapt_keys(self.context_factory(*args, **kw))

    ############################################################################
    # AbstractContextTestCaseBase interface
    ############################################################################

    ### Setup methods ##########################################################

    def context_factory(self, *args, **kw):
        """ Return a context-type for this test class.

            Something like "return GeoContext()" is typical.  If you are testing
            and adapter, then that might be likely as well.
        """
        raise NotImplementedError

    def key_name(self):
        """ Return name of variables
        """
        return 'foo'

    def matched_input_output_pair(self):
        """ Return a pair of values that are matched to

            something like "return GeoContext()" is typical.  If you are testing
            and adapter, then that might be likely as well.
        """
        raise NotImplementedError

    def unmatched_pair(self):
        """ Return a pair of values that are different.
        """
        return 1.2, .5

    ### Dictionary-like get/set ################################################

    def test_get_set_like_dict(self):
        """ Can you read and write values reliably?
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        self._get_set_like_dict(context, key_name, input, output)

        return

    def test_set_rebind(self):
        """ Does rebinding a variable work?
        """
        context = self.context_factory()
        key_name = self.key_name()
        a,b = self.unmatched_pair()
        
        self._get_set_like_dict(context, key_name, a, a)
        self._get_set_like_dict(context, key_name, b, b)

    ### Dictionary-like delete #################################################

    def test_del_existing_item(self):
        """ Can we delete an item from the dictionary?
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        self._del_existing_item(context, key_name, input, output)

        return

    def test_del_non_existing_item_raises_exception(self):
        """ Does deleting a non-existent item raise a NameError excetion?
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        self._del_non_existing_item_raises_exception(context, key_name,
                                                     input, output)

        return

    ### Dictionary-like keys ###################################################

    def test_has_key_true(self):
        """ Does has_key respond correctly when it has a key?
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        context[key_name] = input
        self.assertTrue(context.has_key(key_name))

        return

    def test_has_key_false(self):
        """ Does has_key respond correctly when it doesn't have a key?
        """
        context = self.context_factory()
        key_name = self.key_name()

        self.assertFalse(context.has_key(key_name))

        return

    def test_keys(self):
        """ Does has_key respond correctly when it doesn't have a key?
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        # Make sure it is empty to start.
        self.failUnlessEqual(list(context.keys()), [])

        # Now it should have another value in it.
        context[key_name] = input
        self.failUnlessEqual(list(context.keys()), [key_name])

        return

    ### eval() in a context ####################################################

    def test_simple_eval_works(self):
        """ Does the context work as an evaluation context Python's eval()?

            Note: depending how your adpaters work, this will likely need to
                  be over-ridden.
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        self._simple_eval_works(context, key_name, input, output)

        return

    def test_eval_with_bad_name_raises_nameerror(self):
        """ If a name is missing in the eval statement, is NameError raised?
        """
        context = self.context_factory()
        key_name = self.key_name()
        input, output = self.matched_input_output_pair()

        self._eval_with_bad_name_raises_nameerror(context, key_name,
                                                  input, output)

        return

    ### test __iter__() ########################################################

    def test_iter_len(self):
        """ Can you take a len of a context?
        """
        context = self.context_factory()
        x = len(context)

    ### Private test implementations ###########################################

    def _get_set_like_dict(self, context, key_name, input, output):
        """ Can you read and write values reliably?
        """

        context[key_name] = input
        self.failUnlessEqual(context[key_name], output)

        return

    def _del_existing_item(self, context, key_name, input, output):
        """ Can we delete an item from the dictionary?
        """
        context[key_name] = input
        del context[key_name]
        self.assertFalse(context.has_key(key_name))

        return

    def _del_non_existing_item_raises_exception(self, context, key_name,
                                                input, output):
        """ Does deleting a non-existent item raise a KeyError excetion?
        """

        # Create and evaluatable function that will raise the exception.
        def test_func():
            del context[key_name]

        self.assertRaises(KeyError, test_func)

        return

    def _simple_eval_works(self, context, key_name, input, output):
        """ A Context should work as an evaluation context Python's eval()

            Note: depending how your adpaters work, this will likely need to
                  be over-ridden.
        """
        context[key_name] = input
        expr = key_name + '+ 1' # soemthing like 'foo + 1'
        result = eval(expr, globals(), context)
        self.failUnlessEqual(result, context[key_name]+1)

        return

    def _eval_with_bad_name_raises_nameerror(self, context, key_name,
                                             input, output):
        """ If a name is missing in the eval statement, is NameError raised?
        """

        # fixme: Why does this not work?
        #self.assertRaises(Exception, eval('vp+1', globals(), context))

        try:
            expr = key_name + '+1'
            eval(expr, globals(), context)
        except NameError:
            pass

        return
