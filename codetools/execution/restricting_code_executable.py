from traits.api import (HasStrictTraits, Str, implements, Instance,
        Property)
from traits.protocols.api import adapt
from codetools.blocks.block import Block
from codetools.execution.interfaces import IExecutable
from codetools.contexts.i_context import IContext


class RestrictingCodeExecutable(HasStrictTraits):
    """ IExecutable that executes a piece of code, optionally restricting
    beforehand

    """

    implements(IExecutable)

    # The code to be executed. Read/Write
    code = Property(depends_on='_code')

    # The code to execute.
    _code = Str('pass')

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
            inputs = set()
        if outputs is None:
            outputs = set()

        # filter out and inputs or outputs that are not in the code
        in_and_out = self._block.inputs.union(self._block.outputs)
        filtered_inputs = set(inputs).intersection(in_and_out)
        filtered_outputs = set(outputs).intersection(in_and_out)

        #If called with no inputs or outputs the full block executes
        if filtered_inputs or filtered_outputs:
            block = self._block.restrict(inputs=filtered_inputs,
                    outputs=filtered_outputs)
        else:
            block = self._block
        block.execute(icontext, global_context=globals)
        return block.inputs, block.outputs

    def _set_code(self, new):
        self._block = Block(new)
        self._code = new

    def _get_code(self, new):
        return self._code
