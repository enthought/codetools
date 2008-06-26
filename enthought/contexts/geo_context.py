# Numeric imports
from numpy import ndarray

# ETS imports
from enthought.numerical_modeling.units.api import UnitArray

# Local imports
from data_context import DataContext


class GeoContext(DataContext):
    """ A data context customized to handle geophysics data.
    """

    def allows(self, value, name=None):
        """ We only want Log and ndarray values in our namespace.
        """
        return isinstance(value, (UnitArray, ndarray))


    def get_index_name(self):
        """ Get the index name of the context.
        """

        # Return the first key whose value's units is length-based.
        for name in self.keys():
            if isinstance(self[name], UnitArray) and \
                self[name].units is not None and \
                self[name].units.derivation == (1,0,0,0,0,0,0):
                return name

        return None


    def get_index(self):
        """ Get index of the context
        """

        name = self.get_index_name()
        if name is not None:
            return self[name]
        else:
            return None


# Test
if __name__ == '__main__':
    """ Warning: may raise TraitError due to circular imports.
        However works on python shell.
    """

    from numpy import arange
    from enthought.units.length import feet

    g = GeoContext(name = 'geo')
    g['depth'] = UnitArray(arange(0., 5000., 100.), units = feet)
    g['foo'] = arange(30, 530.0, 10.)

    print g.context_names
    print g.get_index()


### EOF ------------------------------------------------------------------------