Adapted Data Contexts
=====================

Often the data inside a context needs to be transformed in some way before it
is used:

  * possibly in different ways by different parts on an application
  * with different transformations on different variables
  * with multiple different transformations applied sequentially

and the same sequence of transformations may need to be reversed when setting
a value in to the context.  These transformations may even need to be changed
depending on situation or user request.

The AdaptedDataContext provides a framework for applying transformations to
data as it comes in and out of a context.  The AdaptedDataContext provides a
list of adapters in its adapters trait, as well as push and pop methods for
manipulating them.  On getitem, setitem and delitem operations, the
AdapterManagerMixin goes through each of the adapters and first calls the
adapt_name method to perform any manipulations of the name, and then calls
adapt_getitem or adapt_setitem for getitem and setitem operations
respectively.  Once all the adapters have had a chance to perform
transformations, the operation is applied to the underlying context.

To create an adapter all you need to do is to implement the IAdapter interface
by providing at least one of the adapt_name, adapt_getitem, or adapt_setitem
methods.

::

    from numpy import ndarray
    from numpy.fft import fft, ifft
    from enthought.traits.api import HasTraits
    from enthought.contexts.api import IAdapter
    
    class FFTAdapter(HasTraits):
        implements(IAdapter)
        
        def adapt_getitem(self, context, key, value):
            """Take Fourier transform of 1D numpy arrays in the context."""
            if isinstance(value, ndarray) and len(value.shape) == 1:
                return key, fft(value)
        
        def adapt_setitem(self, context, key, value):
            """Take inverse Fourier transform of 1D numpy arrays when setting into
            the context."""
            if isinstance(value, ndarray) and len(value.shape) == 1:
                return key, ifft(value)

The enthought.contexts package contains a number of adapters to perform
operations like masking, unit conversion, and name translation.


