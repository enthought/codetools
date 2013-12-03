#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

from traits.api import (HasStrictTraits, Str, provides, Instance,
        adapt, on_trait_change)
from codetools.blocks.block import Block
from codetools.execution.interfaces import IExecutable
from codetools.contexts.i_context import IContext

@provides(IExecutable)
class RestrictingCodeExecutable(HasStrictTraits):
    """ IExecutable that executes a piece of code, optionally restricting
    beforehand

    """

    # The code to execute.
    code = Str('pass')

    # The block that handles code restriction
    _block = Instance(Block)

    def execute(self, context, globals=None, inputs=None, outputs=None):
        """ Execute code in context, optionally restricting on inputs or
        outputs if supplied

        Parameters
        ----------
        context : Dict-like
        globals : Dict-like, optional
        inputs : List of strings, options
        outputs : List of strings, optional

        Returns
        -------
        inputs : set
            the inputs to the restricted block
        outpus : set
            the outputs of the restricted block

        """
        icontext = adapt(context, IContext)

        if globals is None:
            globals = {}
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        #If called with no inputs or outputs the full block executes
        if inputs or outputs:
            block = self._block.restrict(inputs=inputs, outputs=outputs)
        else:
            block = self._block
        block.execute(icontext, global_context=globals)
        return block.inputs, block.outputs

    @on_trait_change('code')
    def _code_changed(self, new):
        self._block = Block(new)
