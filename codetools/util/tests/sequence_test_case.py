import unittest

from codetools.util.sequence import concat, disjoint, intersect, union
from six.moves import range


class SequenceTestCase(unittest.TestCase):

    def test_concat(self):
        self.assertEqual(
            concat(list(range(i)) for i in range(5)),
            [0, 0, 1, 0, 1, 2, 0, 1, 2, 3],
        )
        self.assertEqual(
            concat([[1,2], [3]]),
            [1, 2, 3],
        )
        self.assertEqual(
            concat([[1, 2, [3,4]], [5,6]]),
            [1, 2, [3, 4], 5, 6],
        )
        self.assertEqual(
            concat([]),
            [],
        )

    def test_union(self):
        self.assertTrue(
            union([set('ab'), set('bc'), set('ac')]) == set('abc'))
        self.assertEqual(union([]), set())

    def test_intersect(self):
        self.assertEqual(
            intersect([set('ab'), set('bc'), set('bb')]),
            set(['b']),
        )
        self.assertEqual(
            intersect([set('ab'), set('bc'), set('ac')]),
            set(),
        )
        with self.assertRaises(StopIteration):
            intersect([])

    def test_disjoint(self):
        self.assertTrue(disjoint(set([1,2]), set([3])))
        self.assertFalse(disjoint(set('abc'), set('xy'), set('z'), set('cde')))
        self.assertTrue(disjoint())
