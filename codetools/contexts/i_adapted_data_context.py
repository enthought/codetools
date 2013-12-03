#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

# Enthought library imports
from traits.api import AdaptsTo, List

# local library imports
from .i_context import IContext
from .adapter.i_adapter import IAdapter


class IAdaptedDataContext(IContext):
    """ A context with adapters.
    """

    #: List of adapters that are used to modify data as it is saved/retreived
    #: from the underlying context.
    adapters = List(AdaptsTo(IAdapter))


    def push_adapter(self, adapter):
        """ Add an adapter to the 'top' of the adapter stack.
        """

    def pop_adapter(self):
        """ Remove the 'top' from the top of the adapter stack.
        """


