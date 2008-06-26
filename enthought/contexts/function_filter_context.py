""" Subclass of DataContext that allows only functions.

Similar to NameFilterContext, however, here it is ensured that only functions
are allowed as values.
"""

# Standard imports
import types
import numpy

# Local imports
from data_context import DataContext


class FunctionFilterContext(DataContext):
    """ This context will only take variables that are functions.
    """

    #### IRestrictedContext interface ##########################################

    def allows(self, value, name=None):
        """ Should allow names according to the DataContext; and only functions
        as values.
        """

        allows_name = super(FunctionFilterContext, self).allows(value, name)
        allows_value = isinstance(value, types.FunctionType) \
                        or isinstance(value, numpy.ufunc)

        return (allows_name and allows_value)


