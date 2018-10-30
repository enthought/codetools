try:
    import tables
except ImportError:
    from nose.plugins.skip import Skip, SkipTest
    raise SkipTest("PyTables not installed")

from codetools.contexts.hdf5_context import Hdf5Context

import numpy as np

import os
import unittest
from nose.tools import assert_equal, assert_not_equal

from six import exec_
from six.moves import range


class Particle(tables.IsDescription):
    identity = tables.StringCol(itemsize=22, dflt=" ", pos=0)  # character String
    idnumber = tables.Int16Col(dflt=1, pos = 1)  # short integer
    speed    = tables.Float32Col(dflt=1, pos = 1)  # single-precision

def create_sample_hdf5_file(filename):
    """From the PyTables website."""
    # Open a file in "w"rite mode
    fileh = tables.open_file(filename, mode = "w")
    # Get the HDF5 root group
    root = fileh.root

    # Create the groups:
    group1 = fileh.create_group(root, "group1")
    group2 = fileh.create_group(root, "group2")

    # Now, create an array in root group
    array1 = fileh.create_array(root, "array1", ["string", "array"], "String array")
    # Create 2 new tables in group1
    table1 = fileh.create_table(group1, "table1", Particle)
    table2 = fileh.create_table("/group2", "table2", Particle)
    # Create the last table in group2
    array2 = fileh.create_array("/group1", "array2", [1,2,3,4])

    # Now, fill the tables:
    for table in (table1, table2):
        # Get the record object associated with the table:
        row = table.row
        # Fill the table with 10 records
        for i in range(10):
            # First, assign the values to the Particle record
            row['identity']  = 'This is particle: %2d' % (i)
            row['idnumber'] = i
            row['speed']  = i * 2.
            # This injects the Record values
            row.append()

        # Flush the table buffers
        table.flush()

    # Finally, close the file (this also will flush all the remaining buffers!)
    fileh.close()

class Hdf5ContextTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        create_sample_hdf5_file('test.h5')

    @classmethod
    def teardown_class(cls):
        os.remove('test.h5')

    def test_empty_keys1(self):
        # test empty keys
        with tables.open_file('test.h5') as table:
            context = Hdf5Context(file_object=table)
            assert_equal(len(list(context.keys())), 0)

    def test_empty_keys2(self):
        # test empty keys
        with tables.open_file('test.h5') as table:
            context = Hdf5Context(file_object=table,
                              path=['root', 'root.group1', 'root.group2'])
            assert_not_equal(len(list(context.keys())), 0)

    def test_get_array1(self):
        # test getting array1 on root
        with tables.open_file('test.h5') as table:
            context = Hdf5Context(file_object=table,
                              path=['root', 'root.group1', 'root.group2'])
            array1 = context['array1']
            assert_equal( len(array1), 2)
            assert_equal( array1, ['string', 'array'])
            assert_equal(context.location('array1'), 'root')

    def test_get_array2(self):
        # test getting array2 on root.group1
        with tables.open_file('test.h5') as table:
            context = Hdf5Context(file_object=table,
                              path=['root', 'root.group1', 'root.group2'])
            array2 = context['array2']
            assert_equal( len(array2), 4)
            assert_equal( array2, [1, 2, 3, 4])
            assert_equal(context.location('array2'), 'root.group1')

    def test_get_table2(self):
        # test getting table2 on group2
        with tables.open_file('test.h5') as table:
            context = Hdf5Context(file_object=table,
                              path=['root', 'root.group1', 'root.group2'])
            table2 = context['table2']
            assert_equal( len(table2), 10)
            assert_equal(context.location('table2'), 'root.group2')

    def test_use_as_context(self):
        # Can we use the context as the namespace of a python calculation?
        from codetools.contexts.api import DataContext, MultiContext

        with tables.open_file('test.h5') as table:
            hdf_context = Hdf5Context(file_object=table,
                              path=['root', 'root.group1', 'root.group2'])
            results = DataContext()
            context = MultiContext(results, hdf_context)
            exec_('array2_plus_one = [a2 + 1 for a2 in array2]', {}, context)
            assert_equal(context['array2_plus_one'], [2, 3, 4, 5])
