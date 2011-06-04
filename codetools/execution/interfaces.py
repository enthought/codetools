""" Interfaces for the execution package.
"""

from traits.api import Bool, Instance, Interface

from codetools.contexts.i_context import IListenableContext


class IExecutable(Interface):
    """ An object that can execute code in a namespace.
    """

    def execute(self, context, globals=None, inputs=None, outputs=None):
        """ Execute the code in the given context.

        Parameters
        ----------
        context : sufficiently dict-like object
            The namespace to execute the code in.
        globals : dict, optional
            The global namespace for the code.
        inputs : list of str, optional
            Names of input variables. These are used to restrict the execution
            to portions of the code that are affected by these inputs.
        outputs : list of str, optional
            Names of output variables. These are used to restrict the execution
            to portions of the code that affect the outputs.
        """


class IExecutingContext(IListenableContext):
    """ A context that manages the execution of a piece of code for another
    context.
    """

    # The underlying context.
    subcontext = Instance(IListenableContext)

    # The executable.
    executable = Instance(IExecutable)

    # Whether to trigger recomputation on 'items_modified' immediately or not.
    defer_execution = Bool(False)


