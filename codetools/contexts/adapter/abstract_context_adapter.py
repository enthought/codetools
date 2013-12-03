#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

from traits.api import HasTraits

""" Base class for all context adapters.

    Actually, this should probably be an AbstractContext...
"""


class AbstractContextAdapter(HasTraits):
    ############################################################################
    # Dictionary interface.
    ############################################################################

    def keys(self):

        raise NotImplementedError

    def has_key(self, name):

        raise NotImplementedError

    def __delitem__(self, name):

        raise NotImplementedError

    def __getitem__(self, name):
        """ Read a value out of the underlying context performing unit
            conversion as necessary.
        """
        raise NotImplementedError

    def __setitem__(self, name, value):
        """ Write a value into the underlying context.
        """
        raise NotImplementedError

