from __future__ import with_statement
from numpy import zeros
from enthought.contexts.with_mask import Mask

dep_len = depth.shape
vp = zeros(dep_len)
vs = zeros(dep_len)
with Mask((depth < 4000.0) & (depth > 1000.0)):
   vp = 1.0
   vs = 1.5
## mgr = Mask((depth < 4000.0) & (depth > 1000.0))
## exit_code = mgr.__exit__
## mgr.__enter__()
## exc = True
## try:
##     try:
##         vp = 1.0
##         vs = 1.5
##     except:
##         exc = False
## finally:
##     if exc:
##         exit_code(None, None, None)
