# Enthought library imports
from enthought.traits.api import HasTraits, Dict, Str

# Local imports
from i_adapter import IAdapter


class NameAdapter(HasTraits):
    """ Maps more descriptive names provided by the user to names in the context
    """

    __implements__ = [IAdapter]

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