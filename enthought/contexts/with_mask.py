""" Using with statement for masking.

Usage in our code-block-context case:
-------------------------------------
Context description:
>>> context['vp'] = ...
>>> context['vs'] = ...
>>> context['depth'] = ...

In the code/script:
>>> from with_mask import Mask
>>> with Mask(depth < 20):
>>>     vp = 1
>>>     vs = 1e-5
>>> <new-block>

* The context definitions should give objects vp and vs to the locals();
    which are arrays.
* Context should be modified in the 'with' block.

References:
-----------
The 'with' statement: http://www.python.org/dev/peps/pep-0343/

Usage:
>>> with EXPR as VAR: # 'as VAR' is optional
>>>     BLOCK
>>>

The with statement translates to:

>>> mgr = (EXPR)
>>> exit = mgr.__exit__
>>> value = mgr.__enter__()
>>> exc = True
>>> try:
>>>     try:
>>>         VAR = value # Only if 'as VAR' is present
>>>         BLOCK
>>>    except:
>>>         exc = False
>>>         if not exit(*sys.exc_info()):
>>>             raise
>>> finally:
>>>    if exc:
>>>        exit(None, None, None)
>>>

Examples:
---------
1. A template for ensuring that a lock, acquired at the start of a block, is
    released when the block is left:

    @contextmanager
    def locked(lock):
        lock.acquire()
        try:
            yield
        finally:
            lock.release()

   Used as follows:

    with locked(myLock):
        # Code here executes with myLock held.  The lock is
        # guaranteed to be released when the block is left (even
        # if via return or by an uncaught exception).

2. Example 1 rewritten without a generator:

    class locked:
       def __init__(self, lock):
           self.lock = lock
       def __enter__(self):
           self.lock.acquire()
       def __exit__(self, type, value, tb):
           self.lock.release()

    (This example is easily modified to implement the other
    relatively stateless examples; it shows that it is easy to avoid
    the need for a generator if no special state needs to be
    preserved.)

Our problem:
------------

The idea here is we are in the block execution environment when the code with
'with' gets executed. We need the adapter to cling onto the context thats the
local environment; and cling off outside the 'with' block/control.

1. We need to check if any change to the 'context' variable in the data context
   will change the context itself.
   -- Checked, It does.
2. Check how the with statement works without a block and context.
    -- Checked, works well.
3. Check how the with statement works during block execution.
    -- Checked, Python crashes on version 2.5.0. However, after upgrading Python
       to 2.5.1., it works well.

"""

# Standard imports
from __future__ import with_statement
from numpy import ndarray
import sys

# Enthought lib imports
from enthought.contexts.i_context import ICheckpointable
from enthought.contexts.data_context import DataContext
from enthought.contexts.multi_context import MultiContext
from enthought.contexts.adapted_data_context import AdaptedDataContext
from enthought.traits.protocols.api import adapt

# Local imports
from with_mask_adapter import WithMaskAdapter

class Mask:
    """ Class that is going to provide the interface between the block and
        context when used with the 'with' keyword.

    """

    mask = ndarray([])
    context = None

    def __init__(self, object):
        """ Initialization method, should always contain a boolean array as a
            mask

            Parameters:
            -----------
            object: Array([Bool])

        """

        self.mask = object


    def __enter__(self):
        """ Enter method.
        """
        locals_val = sys._getframe().f_back.f_locals
        if locals_val.has_key('context') and isinstance(locals_val['context'],
                                                        dict):
            locals_val = locals_val['context']

        # Make a copy of this context.
        locals_val = adapt(locals_val, ICheckpointable).checkpoint()

        adapters = [WithMaskAdapter(mask=self.mask)]
        self.context = AdaptedDataContext(subcontext=locals_val, 
                                          _adapters=adapters)

        return


    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Exit method.
        """
        locals_val = sys._getframe().f_back.f_locals
        if locals_val.has_key('context') and isinstance(locals_val['context'],
                                                        dict):
            locals_val = locals_val['context']

        for k in locals_val.keys():
            if k in self.context.keys() and isinstance(self.context[k],
                                                       ndarray):
                equal_values = self.context[k] == locals_val[k]
                if isinstance(equal_values, ndarray):
                    equal_values = equal_values.all()

                if not equal_values:
                    self.context[k] = locals_val[k]
                    locals_val[k] = self.context[k]

        self.context.pop_adapter()
        return


# Test
if __name__ == '__main__':
#    # 1. Usage without using block and context:
#    from numpy import arange, zeros
#    depth = arange(0., 10000., 1000.)
#    vp = zeros(depth.shape)
#    vs = zeros(depth.shape)
#    with Mask((depth < 4000.0) & (depth > 1000.0)):
#        vp = 1.0
#        vs = 1.5
#    print vp, vs

    # 2. Usage with block and context:
    from numpy import arange, zeros
    from enthought.blocks.api import Block
    dc = DataContext(name='dc')
    context = ParametricContext(dc)
    dc['depth'] = arange(0.,10000., 1000.)
    dc['vp'] = zeros(dc['depth'].shape)
    dc['vs'] = zeros(dc['depth'].shape)
    context['context'] = dc._bindings

    code =  'from __future__ import with_statement\n'\
           'from numpy import zeros\n'\
           'from enthought.contexts.with_mask import Mask\n'\
           'with Mask((depth < 4000.0) & (depth > 1000.0)):vp=1.5 ; vs=1.0'

##     # Expanded form of with statement taken from PEP 343. This is just for testing
##     code =   'from numpy import zeros\n'\
##              'array_len = depth.shape\n'\
##              'vp = zeros(array_len)\n'\
##              'vs = zeros(array_len)\n'\
##              'from enthought.contexts.with_mask import Mask\n'\
##              'mgr = Mask((depth < 4000.0) & (depth > 1000.0))\n'\
##              'exit_code = mgr.__exit__\n'\
##              'mgr.__enter__()\n'\
##              'exc = True\n'\
##              'try:\n'\
##              '    try:\n'\
##              '        vp = 1.0\n'\
##              '        vs = 1.5\n'\
##              '    except:\n'\
##              '        exc = False\n'\
##              'finally:\n'\
##              '    if exc:\n'\
##              '        exit_code(None, None, None)'

    b = Block(code)
    b.execute(context)
    print 'vp', context['vp']
    print 'vs', context['vs']

### EOF ------------------------------------------------------------------------
