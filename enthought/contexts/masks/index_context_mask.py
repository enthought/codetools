""" Class for masking geo_context with conditions on indices
"""

# Standard imports
from __future__ import with_statement
import numpy

# Local imports
from context_mask import ContextMask

#------------------------------------------------------------------------------
#  IndexContextMask class
#------------------------------------------------------------------------------

class IndexContextMask(ContextMask):
    """ Class that is used for implementing with-statement

        The context to be used with the mask should be:
        (a-i) a GeoContext, as, that is the only context which can currently
              have a notion of index.
        (a-ii) any other context which has a get_index() method.
        (b) a context that has a key 'index' in its dictionary.

    """

    def get_indices(self, condition, context):
        """ Condition should be a string saying 'index < <value>'
        """

        indices = []
        index = None
        if hasattr(context, 'get_index'):
            index = context.get_index()
        elif context.has_key('index'):
            index = context['index']

        if index is not None and isinstance(index, numpy.ndarray):
            indices = numpy.where(eval(condition))

        return indices


# Test
if __name__ == '__main__':
    from enthought.contexts.geo_context import GeoContext
    from enthought.numerical_modeling.units.api import UnitArray
    from enthought.units.length import feet

    g = GeoContext(name='geo')
    g['index'] = UnitArray(numpy.arange(0., 5000., 10.), units=feet)
    g['vp'] = numpy.zeros(len(g['index']), numpy.float)
    g['vs'] = numpy.zeros(len(g['index']), numpy.float)
    threshold = 3000.0

    # Usage
    with IndexContextMask(g, 'index < threshold', {'vp': 1.5, 'vs':1e-5}):
        # These should be the new values.
        print g['vp']
        print g['vs']

    # These should be the original values.
    print g['vp']
    print g['vs']


### EOF ------------------------------------------------------------------------