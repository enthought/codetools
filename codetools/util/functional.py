#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
'Non-standard higher-order functions'

from functools import partial

from six.moves import reduce


def compose(*fs):
    ''' ``compose(f,g,...,h)(*args, **kw) == f(g(...(h(*args, **kw))))``

        >>> compose(len, str)(100)
        3
        >>> compose(len, str, len, str)(1234567890)
        2
        >>> compose()(1)
        1
        >>> list(map(compose(sum, range, len), ['foo', 'asdf', 'wibble']))
        [3, 6, 15]
    '''

    if len(fs) == 0:
        return lambda x: x

    binary_compose = lambda f,g: lambda *args, **kw: f(g(*args, **kw))
    return reduce(binary_compose, fs)
