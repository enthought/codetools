""" Test cases for functions in utils
"""

# Standard imports
import unittest
from numpy import array, ndarray

# Utils imports
from enthought.contexts.utils import compare_objects, safe_repr


class TrivialNDArraySubclass(ndarray):
    """ Make sure comparisons between subclasses of ndarrays are handled
    correctly.
    """

class UtilsTestCase(unittest.TestCase):
    """ Test all functions in the utils module
    """

    ### compare_objects tests ------------------------------------------------
    
    def test_compare_dicts(self):
        """ Check if dictionaries are compared correctly.
        """

        d1 = {'a':1, 'b':2, 'c':[1,2,3]}
        d2 = {'a':1, 'b':2, 'c':[1,2,3]}

        self.assertFalse(compare_objects(d1, {'a':1, 'b':3}))
        self.assertFalse(compare_objects(d1, {'a':1, 'd':4}))
        self.assertFalse(compare_objects(d1, {'a':1, 'b':2, 'c':3, 'd':4}))
        self.assertFalse(compare_objects(d1, {'a':1, 'b':2, 'c':[1,2]}))
        self.assertFalse(compare_objects(d1, {'a':1, 'b':2, 'c':(1,2,3,4)}))
        self.assertTrue(compare_objects(d1, d2))

    def test_compare_lists(self):
        """ Check if lists are compared correctly
        """

        l1 = [1,2,3,{'a':1,'b':2},(1,2,3)]
        l2 = [1,2,3,{'a':1,'b':2},(1,2,3)]

        self.assertTrue(compare_objects(l1, l2))
        self.assertFalse(compare_objects(l1, [1,2,3, set([1,2,3]), (1,2,3)]))
        self.assertFalse(compare_objects(l1, [1,2]))
        self.assertFalse(compare_objects(l1, [1,2,3, {'a':1}, (1,2,3)]))
        self.assertFalse(compare_objects(l1, [1,2,3, {'a':1, 'b':2}, (1,2)]))


    def test_compare_sets(self):
        """ Check if sets are compared correctly
        """

        s1 = set([1,2,3,(1,2,3)])
        s2 = set([1,2,3,(1,2,3)])

        self.assertTrue(compare_objects(s1, s2))
        self.assertFalse(compare_objects(s1, set([1,2])))
        self.assertFalse(compare_objects(s1, set([1,2,3,(1,2)])))

    def test_compare_tuples(self):
        """ Check if tuples are compared correctly
        """

        t1 = (0.25, array([1,2,3,4]))
        t2 = (0.25, array([1,2,3,4]))

        self.assertTrue(compare_objects(t1, t2))
        self.assertFalse(compare_objects(t1, (0.25, 0.5, 0.75)))
        self.assertFalse(compare_objects(t1, (0.25, array([1,2,3]))))
        self.assertFalse(compare_objects(t1, (0.25, [1,2,3,4])))

    def test_compare_misc(self):
        """ Check other miscellaneous compares.
        """

        self.assertFalse(compare_objects({'a':1, 'b':2}, (1,2)))
        self.assertFalse(compare_objects(array([1,2,3]), array([1,3,4])))
        self.assertTrue(compare_objects(array([1,2,3]), array([1,2,3])))
        self.assertFalse(compare_objects(array([1,2,3]), array([1,2])))

    def test_compare_ndarray_subclasses(self):
        """ Check that subclasses of ndarray are handled with the ndarray
        branch.
        """
        a1 = array([1,2,3]).view(TrivialNDArraySubclass)
        a2 = array([1,3,4]).view(TrivialNDArraySubclass)
        a3 = array([1,2,3]).view(TrivialNDArraySubclass)
        a4 = array([1,2]).view(TrivialNDArraySubclass)
        self.assertFalse(compare_objects(a1, a2))
        self.assertTrue(compare_objects(a1, a3))
        self.assertFalse(compare_objects(a1, a4))

    def test_safe_repr(self):
        """ Does safe_repr limit the amount of characters in a repr?
        """
        short = 'abcdefghij'
        long = short * 10
        longer = long * 10
        self.assertEqual(repr(short), safe_repr(short, limit=100))
        self.assertEqual(repr(long), safe_repr(long, limit=1000))
        self.assertNotEqual(repr(longer), safe_repr(longer, limit=100))
        self.assertTrue(len(safe_repr(longer, limit=100)) < 110)

                                        
if __name__ == '__main__':
    import sys
    unittest.main(argv = sys.argv)
    
### EOF -----------------------------------------------------------------------
