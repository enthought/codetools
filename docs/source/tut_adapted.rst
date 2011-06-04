Adapted Data Contexts
=====================

Often the data inside a context needs to be transformed in some way before it
is used:

* possibly in different ways by different parts on an application
* with different transformations on different variables
* with multiple different transformations applied sequentially

And the same sequence of transformations may need to be reversed when setting
a value in to the context. These transformations may even need to be changed
depending on the situation or a user request.

The AdaptedDataContext class provides a framework for applying transformations
to data as it comes in and out of a context. AdaptedDataContext provides a list
of adapters in its :attr:`adapters` trait attribute, as well as :meth:`push` and
:meth:`pop` methods for manipulating them. On get, set, or delete operations,
the AdapterManagerMixin goes through each of the adapters and first calls the
:meth:`adapt_name` method to perform any manipulations of the name, and then
calls :meth:`adapt_getitem` or :meth:`adapt_setitem` for get and set
operations respectively. Once all the adapters have had a chance to perform
transformations, the operation is applied to the underlying context.

To create an adapter all you need to do is to implement the IAdapter interface
by providing at least one of the :meth:`adapt_name`, :meth:`adapt_getitem`, or
:meth:`adapt_setitem` methods.

::

    from numpy import ndarray
    from numpy.fft import fft, ifft
    from traits.api import HasTraits
    from enthought.contexts.api import IAdapter
    
    class FFTAdapter(HasTraits):
        implements(IAdapter)
        
        def adapt_getitem(self, context, key, value):
            """Take Fourier transform of 1-D Numpy arrays in the context."""
            if isinstance(value, ndarray) and len(value.shape) == 1:
                return key, fft(value)
        
        def adapt_setitem(self, context, key, value):
            """Take inverse Fourier transform of 1D numpy arrays when setting into
            the context."""
            if isinstance(value, ndarray) and len(value.shape) == 1:
                return key, ifft(value)

The :mod:`enthought.contexts` package contains a number of adapters to perform
operations like masking, unit conversion, and name translation.


