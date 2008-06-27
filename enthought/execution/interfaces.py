""" Interfaces for the execution package.
"""

from enthought.traits.api import Bool, Instance, Interface

from enthought.contexts.i_context import IListenableContext


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
        outputs : list of str, optional
            Names which may be used to restrict the execution to portions of the
            code. Ideally, only code that is affected by the inputs variables
            and affects the outputs variables will be executed.
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


