# Copyright (c) 2007-2013 by Enthought, Inc.
# All rights reserved.

try:
    from ._version import full_version as __version__
except ImportError:
    __version__ = 'not-built'

__requires__ = [
    'traits',
]
