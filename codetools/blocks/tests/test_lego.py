'''
Created on Aug 5, 2011

@author: sean
'''
import unittest

from codetools.blocks.smart_code import SmartCode
from codetools.blocks.lego import split, join, sort as sort_blocks, DependencyCycleError
from codetools.blocks.tests import assert_block_eq
from itertools import permutations


class TestSplit(unittest.TestCase):

    def test_simple(self):
        block = SmartCode('a = 1; b = 2')

        expected1 = SmartCode('a = 1')
        expected2 = SmartCode('b = 2')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 2)
        sb2, sb1 = block_list

        assert_block_eq(self, sb1, expected1)
        assert_block_eq(self, sb2, expected2)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 2)

        sb1, sb2 = block_list

        assert_block_eq(self, sb1, expected1)
        assert_block_eq(self, sb2, expected2)

    def test_augment(self):
        block = SmartCode('a = 1; a += 2')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 1)
        sb1, = block_list

        assert_block_eq(self, sb1, block)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 1)

        sb1, = block_list

        assert_block_eq(self, sb1, block)

    def test_augment2(self):

        block = SmartCode('a = 1; a += 2; b = 2')

        expected1 = SmartCode('a = 1; a += 2')
        expected2 = SmartCode('b = 2')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 2)
        sb2, sb1 = block_list

        assert_block_eq(self, sb1, expected1)
        assert_block_eq(self, sb2, expected2)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 2)

        sb1, sb2 = block_list

        assert_block_eq(self, sb1, expected1)
        assert_block_eq(self, sb2, expected2)

    def test_augment3(self):
        block = SmartCode('a = 1; b = 2; a += 2')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 1)
        sb1, = block_list

        assert_block_eq(self, sb1, block)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 1)

        sb1, = block_list

        assert_block_eq(self, sb1, block)

    def test_assignX(self):

        block = SmartCode('a = 1; b = a; a = b + 2')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 1)
        sb1, = block_list

        assert_block_eq(self, sb1, block)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 1)

        sb1, = block_list

        assert_block_eq(self, sb1, block)

    def test_for(self):
        block = SmartCode('a = 1\nfor i in j: k')

        expected1 = SmartCode('a = 1')
        expected2 = SmartCode('for i in j: k')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 2)
        sb2, sb1 = block_list

        assert_block_eq(self, sb1, expected1)
        assert_block_eq(self, sb2, expected2)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 2)

        sb1, sb2 = block_list

        assert_block_eq(self, sb1, expected1)
        assert_block_eq(self, sb2, expected2)

    def test_for_augment(self):
        block = SmartCode('a = 1\nfor i in j: a+=1')

        block_list = list(split(block, reversed=True))

        self.assertEqual(len(block_list), 1)
        sb1, = block_list

        assert_block_eq(self, sb1, block)

        block_list = list(split(block, reversed=False))

        self.assertEqual(len(block_list), 1)

        sb1, = block_list

        assert_block_eq(self, sb1, block)


class TestJoin(unittest.TestCase):

    def test_join_one(self):

        block = SmartCode('a')

        b2 = join([block])

        assert_block_eq(self, block, b2)

    def test_join_two(self):

        block1 = SmartCode('a')
        block2 = SmartCode('b')


        b2 = join([block1, block2])

        expected = SmartCode('a;b')
        assert_block_eq(self, expected, b2)


class TestSort(unittest.TestCase):

    def test_sort_one(self):
        block = SmartCode('a')
        sorted_blocks = sort_blocks([block])

        self.assertEqual(len(sorted_blocks), 1)

        self.assertIs(block, sorted_blocks[0])

    def test_sort_simple(self):
        block1 = SmartCode('a = 1')
        block2 = SmartCode('b = a')


        for seq_of_blocks in permutations([block1, block2]):
            sorted_blocks = sort_blocks(seq_of_blocks)

            self.assertEqual(sorted_blocks, [block1, block2])

    def test_sort_three(self):
        block1 = SmartCode('x = 1')
        block2 = SmartCode('b = x')
        block3 = SmartCode('c = b + x')

        for seq_of_blocks in permutations([block1, block2, block3]):
            sorted_blocks = sort_blocks(seq_of_blocks)

            self.assertEqual(sorted_blocks, [block1, block2, block3])

    def test_cycle(self):

        block2 = SmartCode('b = x')
        block3 = SmartCode('x = b')

        seq_of_blocks = [block2, block3]

        with self.assertRaises(DependencyCycleError):
            sort_blocks(seq_of_blocks)

    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_split_simple']
    unittest.main()
