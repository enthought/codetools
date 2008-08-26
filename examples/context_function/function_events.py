""" This example demonstrates how we can use a data context and context
function, together with Traits events to observe the internals of a function
as it executes.
"""

from enthought.traits.api import HasTraits, on_trait_change
from enthought.contexts.api import DataContext, context_function

class ListeningDataContext(DataContext):
    @on_trait_change('items_modified')
    def print_event(self, event):
        print "items_modified:"
        for added in event.added:
            print "  added:", added, "=", self[added]
        for modified in event.modified:
            print "  modified:", modified, "=", self[modified]
        for removed in event.removed:
            print "  removed:", removed

def f(x):
    y = x+2
    y += 1
    z = 12
    del z
    return y

f = context_function(f, ListeningDataContext)

f(3)