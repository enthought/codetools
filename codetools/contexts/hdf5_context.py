#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

from traits.api import HasTraits, List, Str, Property, Any, provides
from codetools.contexts.api import IRestrictedContext

import tables

@provides(IRestrictedContext)
class Hdf5Context(HasTraits):
    """ Provide a "context" (partial dictionary interface) into an HDF5
        file.  It allows multiple paths, specified by the path list, within
        the file to be treated as a single namespace.

        fixme: We probably also want this to support looking into
               structured arrays that are leaves in an HDF file and using
               their fields as part of the namespace.

        Example:
        <fixme>

    """

    # The HDF file with the data available through this context.
    file_object = Any

    # "Directories" in the Hdf5 file to use as namespaces.
    # The paths are specified using '.' notation.
    # fixme: use dot or slash notation?  foo.bar or /foo/bar?
    path = List(Str)


    # The HDF file name or object that is referred to by this context.
    # fixme: Add this to allow a single place to set either name or object.
    #file = Property

    # The HDF file name that is referred to by this context.
    # fixme: Add this.
    #file_name = Any

    # List of paths in the path directory that are not found
    # in this Hdf5 file.
    # fixme: Add this later.
    #unavailable_paths = List(Str)

    # fixme: Add a "name map" to map requested names to hdf5 names.
    #        Or, this may be a higher level things we add somewhere else...

    # fixme: Detect name conflicts where the same variable is found in
    #        different paths.  This isn't an error, but it is worth a warning.

    ##########################################################################
    # Hdf5Context Interface
    ##########################################################################

    def location(self, name):
        """ return the path where name is found.  If it isn't in the context,
            return None.

            Currently used in testing to ensure that we are finding values
            fromt the expected location.
        """
        location = None
        for dir in self.path:
            # fixme: how do you do this 'correctly' in tables?
            node_str = '.'.join(['self.file_object', dir])
            try:
                node = eval(node_str)
                if name in node._v_children.keys():
                    location = dir
                    break
            except tables.NoSuchNodeError:
                continue

        return location


    ##########################################################################
    # IRestrictedContext Interface
    ##########################################################################

    def allows(self, value, name=None):
        # fixme: We shouldn't ever get to this point in a context at the
        #        moment.
        raise NotImplementedError


    ##########################################################################
    # Dictionary Interface
    ##########################################################################

    def keys(self):
        """ Return a list of the names available in the namespace.
        """
        all_names = set()

        for dir in self.path:
            # fixme: how do you do this 'correctly' in tables?
            node_str = '.'.join(['self.file_object', dir])
            try:
                node = eval(node_str)
                all_names.update(node._v_leaves.keys())
            except tables.NoSuchNodeError:
                continue

        ordered_names = sorted(all_names)
        return ordered_names

    def iteritems(self):
        """Return an iterator of the (key,value) pairs in the namespace
        """
        # Fixme: Extract and share (and improve) tree-walking code in keys()
        return ((k, self.__getitem__(k)) for k in self.keys())

    def __contains__(self, name):
        return name in self.keys()

    def __getitem__(self, name):
        """
        """

        node = None

        # naive walk through all paths to find the variable.
        # fixme: I'm sure this can be improved 10-100 fold.
        for dir in self.path:
            # Convert a dir such as 'root.foo.bar' to '/foo/bar'.
            slash_dir = '/' + '/'.join(dir.split('.')[1:])
            try:
                node = self.file_object.getNode(slash_dir, name)
            except tables.NoSuchNodeError:
                continue

        if node is not None:
            # Get the value for the node
            value = node.read()
            # FIXME: Eventually, we should replace the previous line with
            # something like the following code, if we want to memory-map
            # numpy arrays.
            #if isinstance(node, tables.Array):
            #    if node.atom.shape == ():
            #        # Read scalars
            #        value = node.read()
            #    else:
            #        value = node
            #else: # node is not an Array.
            #    value = node
        else:
            raise KeyError("'%s' not found" % name)

        return value

    def __setitem__(self, name, value):
        """ Write an item from the context.

            For now we will not support this feature within
            an Hdf5 context.  All writes should be dealt
            occur into a copy-on-write context coupled with
            this one.
        """
        raise NotImplementedError


    def __delitem__(self, name):
        """ Delete an item from the context.

            For now we will not support this feature within
            an Hdf5 context.  All deletes should be dealt
            occur into a copy-on-write context coupled with
            this one.
        """
        raise NotImplementedError

