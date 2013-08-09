#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#

from __future__ import absolute_import

# Enthought library imports
from traits.api import HasTraits, Dict, Str, provides

# Local imports
from .i_adapter import IAdapter

@provides(IAdapter)
class NameAdapter(HasTraits):
    """ Maps more descriptive names provided by the user to names in the context
    """

    #########################################################################
    # NameAdapter traits
    #########################################################################

    map = Dict(Str, Str)


    ###########################################################################
    # IAdapter interface.
    ###########################################################################

    def adapt_name(self, context, name):
        """ Given a name, see if it is an alias in the map table. If it is not,
            the unaltered name should be in the context. Note that if a name is
            listed both as an alias and as an actual variable in the context,
            the unaltered name will be used.
        """

        if name in self.map and name not in context:
            return self.map[name]
        else:
            return name

    def adapt_keys(self):
        """ Returns a list containing any keys (names) defined by this
            adapter.
        """
        return self.map.keys()
