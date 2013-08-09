""" Class for masking geo_context with conditions on indices
"""

from __future__ import absolute_import

# Standard imports
import numpy

# Local imports
from .context_mask import ContextMask

#------------------------------------------------------------------------------
#  IndexContextMask class
#------------------------------------------------------------------------------

class IndexContextMask(ContextMask):
    """ Class that is used for implementing ``with``-statement

        The context to be used with the mask should be:

        - One of:

          * A GeoContext, as that is the only context which can currently
            have a notion of index.
          * Any other context which has a get_index() method.

        - A context that has a key 'index' in its dictionary.

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
    from codetools.contexts.geo_context import GeoContext
    from scimath.units.api import UnitArray
    from scimath.units.length import feet

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
