""" This example demonstrates how we can use a data context and context
function, together with Traits events to observe the internals of a function
as it executes.
"""

from traits.api import HasTraits, on_trait_change
from codetools.contexts.api import DataContext, context_function

class ListeningDataContext(DataContext):
    """ A simple subclass of DataContext which listens for items_modified
    events and pretty-prints them."""

    @on_trait_change('items_modified')
    def print_event(self, event):
        print "Event: items_modified"
        for added in event.added:
            print "  Added:", added, "=", repr(self[added])
        for modified in event.modified:
            print "  Modified:", modified, "=", repr(self[modified])
        for removed in event.removed:
            print "  Removed:", removed

def f(x, t=3):
    """ A function which will fire add, modify and delete events. """
    y = x+2
    y += 1
    z = '12'
    del z
    return y

f = context_function(f, ListeningDataContext)

f(3)
