MultiContexts
=============

There is one notable issue with the application shown in
:ref:`traitslikecontextwrapper`: the UI assumes that every input is a float, and
that every output should be displayed. 

Suppose we try to use a slightly modified version of the code block from
:ref:`rocket-restriction-example` section with that application::

    from numpy import array, ones
    
    def simple_integral(y, x):
        """Return an array of trapezoid sums of y"""
        dx = x[1:] - x[:-1]
        if array(y).shape == ():
            y_avg = y*ones(len(dx))
        else:
            y_avg = (y[1:]+y[:-1])/2.0
        integral = [0]
        for i in xrange(len(dx)):
          integral.append(integral[-1] + y_avg[i]*dx[i])
        return array(integral)

    thrust = fuel_density*fuel_burn_rate*exhaust_velocity + nozzle_pressure*nozzle_area
    mass = mass_rocket + fuel_density*(fuel_volume - simple_integral(fuel_burn_rate,t))
    acceleration = thrust/mass
    velocity = simple_integral(acceleration, t)
    momentum = mass*velocity
    displacement = simple_integral(velocity, t)
    kinetic_energy = 0.5*mass*velocity**2
    work = simple_integral(thrust, displacement)

We would discover that the function :func:`simple_integral` appears in the list
of outputs. The reason that this function appears as an output is that, as far
as a namespace is concerned, defining a function is the same as assigning to a
variable. Also note that the imports *don't* appear --- imported names are
available in the :attr:`fromimports` trait attribute of a Block and don't appear
as outputs.

So one solution to this problem is to always import functions.  However there
is a second problem: the variable *t* needs to be an array, not a float, and
we probably shouldn't have the user interacting with it directly anyway.
So we need to solve the more general problem of which outputs should be
displayed.

There are several approaches to solving this problem, but perhaps the most
elegant is to have the DataContext itself keep track.  One way to achieve
this is through the use of a MultiContext, which is a context that contains
a number of subcontexts, together with rules to decide which of these it
should use for a particular variable. To an external viewer, the MultiContext
appears just like a DataContext, but objects can keep references to particular
subcontexts that supply the information that they require.

The subcontexts need to be able to tell the MultiContext which items they can
accept, and which they do not wish to store. To do this they implement the
IRestrictedContext interface, which simply means that they have to provide
an :meth:`allows` method which should take a key and value as input and
return True if the Context accepts the item. Regular DataContext objects
implement the IRestrictedContext interface, deferring to their subcontext if it
is a DataContext, but allowing any variable to be set otherwise.

Let's say that we want to have a context available which contains only
variables whose values are floats.  That would be done like this::

    >>> from codetools.contexts.api import MultiContext
    >>> class FloatContext(DataContext):
    ...     def allows(key, value):
    ...         return isinstance(value, float)
    >>> class BContext(DataContext):
    ...     def allows(key, value):
    ...         return key[0] == "b"
    >>> float_context = FloatContext()
    >>> b_context = BContext()
    >>> default_context = DataContext() # subcontext is a dict, so allows() is always True
    >>> multi_context = MultiContext(float_context, b_context, default_context)
    >>> multi_context['a'] = 34.0
    >>> multi_context['b'] = 34
    >>> multi_context['c'] = "Hello"
    >>> multi_context.items()
    [('a', 34.0), ('b', 34), ('c', 'Hello')]
    >>> float_context.items()
    [('a', 34.0)]
    >>> b_context.items()
    [('b', 34)]
    >>> default_context.items()
    [('c', 'Hello')]

.. note::
    There are some wrinkles to the way that the MultiContext handles setting an
    item when multiple subcontexts will accept it::
    
        >>> multi_context['c'] = 10.0
        >>> multi_context['c']
        10.0
        >>> float_context['c']
        10.0
        >>> default_context['c']
        'Hello'
    
    There are also some wrinkles in how it handles matching keys in contexts
    that won't accept an item::
    
        >>> multi_context['a'] = "Goodbye"
        >>> multi_context['a']
        "Goodbye"
        >>> default_context['a']
        "Goodbye"
        >>> "a" in float_context
        False
        >>> default_context['b'] = "foo"
        >>> multi_context['b'] = "bar"
        >>> multi_context['b']
        'bar'
        >>> 'b' in default_context
        True
        >>> default_context['b']
        'foo'
    
    Note that if a context rejects an item, the MultiContext removes the key
    for that item from the rejecting context. If a context accepts an item,
    and the same key exists in later contexts (in the context list), the items
    with that key in the later contexts are untouched.
    
    If this sort of behavior is not what you want, then you can easily subclass
    MultiContext to provide the semantics that your application requires.

Using a MultiContext in the Block-Context-Execution Manager pattern allows us
to have the Execution Manager looking only at the inputs, and allows us to
separate out the UI from the Execution Manager.



