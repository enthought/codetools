#
# (C) Copyright 2011-13 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
"""
Recompile
=========

Code to create a .pyc in a version-safe manner.

Created on Nov 3, 2011

Author: Sean Ross-Ross

"""

import os
import sys
import struct
from time import time

py3 = sys.version_info.major >= 3

if py3:
    import builtins  # @UnresolvedImport
else:
    import __builtin__ as builtins

import marshal
import imp
from py_compile import PyCompileError, wr_long

MAGIC = imp.get_magic()


def create_pyc(codestring, cfile, timestamp=None):
    """ Create a .pyc in a version-safe manner

    Parameters
    ----------

    codestring:
        The code to compile into the .pyc

    cfile:
        An open .pyc file object.

    timestamp:
        An optional timestamp (in seconds since the epoch).  Default is now.

    """

    if timestamp is None:
        timestamp = time()

    codeobject = builtins.compile(codestring, '<recompile>', 'exec')

    cfile.write(MAGIC)
    cfile.write(struct.pack('i', timestamp))
    marshal.dump(codeobject, cfile)
    cfile.flush()
