# Standard library imports
import copy

# Enthought library imports
from enthought.traits.api import Any

# Local imports
from data_context import DataContext


class NameFilterContext(DataContext):
    """ This context will only take variables that match a list of names.

    The name of the variable is compared to a list of names.  If it matches one
    of them, it is allowed into the context.  If it doesn't, it isn't allowed in
    the context.
    """

    ##########################################################################
    # NameFilterContext interface
    ##########################################################################

    # The list of names that are allowed into this context.
    names = Any(copy='shallow')  #List -- any container that supports 'in' will work.


    def _names_default(self):
        return []

    #### IRestrictedContext interface ##########################################

    def allows(self, value, name=None):
        """ Return False if the name is not in our list of accepted names.
        """
        result = name in self.names

        return result

