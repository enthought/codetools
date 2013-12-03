#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
""" Provides tools for organizing objects into namespaces:
    namespace: decorator
    namespace_from_keywords: function
"""
from __future__ import absolute_import

from .decorators import func2str

##############################################################################
# Public Interface
##############################################################################

def namespace_from_keywords(**kw):
    """ Return a namespace containing an attribute matching each kw argument.
    Example:

    >>> numbers = namespace_from_keywords( little=1, medium=3, big=99)
    >>> numbers.little
    1
    >>> numbers.medium
    3
    >>> numbers.big
    99
    """
    return Namespace(kw)


def namespace(function):
    """ Decorator that makes a function return a Namespace object with all
        its local variables among its attributes. This provides a way to
        easily generate names which look like container.variable1,
        container.variable2,... without using the full dot notation
        when the sub-variables (sub-objects) are created.

        >>> @namespace
        ... def quad(x, a=1, b=2,c=3):
        ...     y = a*x**2 + b*x + c
        >>> results = quad(2)
        >>> results.a
        1
        >>> results.b
        2
        >>> results.c
        3
        >>> results.x
        2
        >>> results.y
        11
        """

    # FIXME:? will not work in exec'd code, because func2str needs to read
    # the source file.
    # BUT works in execfile, so perhaps not important in practice.

    arg_names, defaults = args_and_keywords(function)

    s = func2str(function, backframes=2)
    code_object = compile(s, 'anonymous', 'exec')

    # fixme: Make the returned function have the same signature
    #        as the passed in function.
    def namespace_function(*args, **kw):

        # The namespace should default to the function's keyword arguments.
        ns = defaults.copy()
        ns.update(kw)

        positional = dict(zip(arg_names, args))
        ns.update(positional)
        globs = function.func_globals

        exec code_object in globs, ns

        # Save the original function name in the namespace as
        # the attribute '_func_name'.
        ns['_func_name'] = function.__name__

        return Namespace(ns)

    return namespace_function


class Namespace(object):
    """ Make a dictionary of variables accesible through a attribute lookup.

        The namespace object initializer takes a dictionary as its only
        argument.  Any variables in the dictionary will be available as
        attributes on the object.

        Example:
            >>> d = {'a':1, 'b':2}
            >>> namespace = Namespace(d)
            >>> namespace.a
            1
            >>> namespace.b
            2
    """

    def __init__(self, namespace):
        self.__dict__.update(namespace)


    def __iter__(self):
        """Returns iterator over (name, object) pairs in the namespace
        Reasons to do this instead of iteritems:
        1. Don't pollute the namespace with non-user "__" names.
        2. Cleaner user code.
        Reason not to:
        1. This is a view of a dictionary and when you iterate on
        a dictionary you get keys.
        """
        return self.__dict__.iteritems()

    def __getitem__(self, key):
        """ Support attribute access by index notation (square brackets).
        """
        return self.__dict__[key]

    def __setitem__(self, key, value):
        """ Support attribute access by index notation (square brackets).
        """
        self.__dict__[key] = value


##############################################################################
# Utilities
##############################################################################

def args_and_keywords(function):
    """ Return the information about the function's argument signature.

        Return a list of the function's positional argument names and a
        dictionary containing the function's keyword arguments.

        Example:
            >>> import random
            >>> args, kw = args_and_keywords(random.triangular)
            >>> args
            ('self', 'low', 'high', 'mode')
            >>> sorted(kw.items())
            [('high', 1.0), ('low', 0.0), ('mode', None)]

    """
    arg_count = function.func_code.co_argcount
    arg_names = function.func_code.co_varnames[:arg_count]
    try:
        kw_arg_count = len(function.func_defaults)
        kw_names = arg_names[-kw_arg_count:]
        kw_dict = dict(zip(kw_names, function.func_defaults))
    except TypeError:
        kw_dict = {}

    return arg_names, kw_dict


if __name__ == "__main__":
    import doctest
    doctest.testmod()
