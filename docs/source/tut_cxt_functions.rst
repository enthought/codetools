Context Functions
=================

It should be clear by this point that the ability to use a general context
as the namespace when executing code permits some complex behaviors to be
implemented simply. There are circumstances where it would be useful to
replace the namespace of a function with a context.  The :mod:`context_function`
module provides some tools for doing this.

This example shows how to set up a simple listening data context that displays
changes within a function's local namespace as it executes::

	from traits.api import HasTraits, on_trait_change
	from enthought.contexts.api import DataContext, context_function
	
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
	    """ A function which fires add, modify and delete events. """
	    y = x+2
	    y += 1
	    z = '12'
	    del z
	    return y
	
	f = context_function(f, ListeningDataContext)

The functionality is also available as a function decorator::

	@local_context(ListeningDataContext)
	def f(x, t=3):
	    """ A function which will fire add, modify and delete events. """
	    y = x+2
	    y += 1
	    z = '12'
	    del z
	    return y

The :func:`context_function` and :func:`local_context` functions both take an
argument which is a context factory: each invocation of the function results in
a call to the context factory. In most cases it returns a freshly created
context.
