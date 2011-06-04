from __future__ import with_statement
from numpy import arange, zeros
from enthought.contexts.with_mask import Mask

dep_len = depth.shape
vp = zeros(dep_len)
vs = zeros(dep_len)
with Mask((depth < 4000.0) & (depth > 1000.0)):
   vp = arange(0., 10., 1.)
   vs = arange(0., 100., 10.)
## mgr = Mask((depth < 4000.0) & (depth > 1000.0))
## exit_code = mgr.__exit__
## mgr.__enter__()
## exc = True
## try:
##     try:
##         vp = arange(0., 10., 1.)
##         vs = arange(0., 100., 10.)
##     except:
##         exc = False
## finally:
##     if exc:
##         exit_code(None, None, None)
