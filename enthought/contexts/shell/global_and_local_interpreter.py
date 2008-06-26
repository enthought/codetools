""" Interpreter that uses a NumericContext as its namespace for execution.
"""

# Standard library imports
import sys, re
from code import softspace

# wx Library imports
# fixme: Get rid of this when we can..
from wx.py.interpreter import Interpreter

# ETS imports
from enthought.numerical_modeling.numeric_context.api import NumericContext, \
    EventDict


# regular expression to find "from xyz import *"
import_all = re.compile(r"^from\s\s*.*\s\s*import\s\s*\*")

class GlobalAndLocalInterpreter(Interpreter):
    """ Evaluate expressions in both a global and local namespace.

        The global namespace must be a dictionary object.  The local namespace
        can be anything that has a dictionary interface
        (ie. __delitem__, __getitem__, and __setitem__).
        By default, the local dictionary defaults to a NumericContext.
    """

    ############################################################################
    # object interface
    ############################################################################

    def __init__(self, locals=None, globals=None, rawin=None,
                 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        """ Constructor.

        The optional 'locals' argument specifies a context in which
        the code is executed; it defaults to a newly created
        NumericContext.  The optional globals argument is the global namespace
        for function evaluation.  Note that, unlike locals, this *must* be
        dictionary.  This is so that 'from xyz import *' will work.

        The variable "__name__" is set to "__console__" and "__doc__"
        is set to None.
        """

        if globals is None:
            self.globals = {}
        else:
            # The global namespace must be a dictionary.
            assert(isinstance(globals, dict))
            self.globals = globals

        # Set up a few standard variables in the context.
        self.globals["__name__"] = "__console__"
        self.globals["__doc__"] = None

        if locals is None:
            # The default "primary" namespace for the context is the same
            # as our global dict.
            self.locals = locals = NumericContext(context_data=EventDict(self.globals))
        Interpreter.__init__(self, locals=locals, rawin=rawin,
                             stdin=stdin, stdout=stdout, stderr=stderr)


    ############################################################################
    # Interpreter interface
    ############################################################################

    def runsource(self, source, filename="<input>", symbol="single"):
        """ Compile and run some source in the interpreter.
        """

        # fixme: This is a lot of cut/paste programming because we want to
        # override some behavior that is both in Interpreter.runsource, but
        # pyshell interpreter also has some customization it.  We duplicate
        # a lot of this to add a single if statement.
        # code.InteractiveInterpeter's runsource is now in _runsource.  This
        # is a duplication of the py.Interpeter.runsource with a change to call
        # _runsouce.  sigh.  We need to re-write a lot of the shell we are
        # relying on -- with IPython...

        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = \
                   self.stdin, self.stdout, self.stderr

        more = self._runsource(source, filename, symbol)

        # If sys.std* is still what we set it to, then restore it.
        # But, if the executed source changed sys.std*, assume it was
        # meant to be changed and leave it. Power to the people.
        if sys.stdin == self.stdin:
            sys.stdin = stdin
        if sys.stdout == self.stdout:
            sys.stdout = stdout
        if sys.stderr == self.stderr:
            sys.stderr = stderr
        return more

    def _runsource(self, source, filename="<input>", symbol="single"):
        """ This is cut/pasted from code.Interpreter.  We've just added the
            regex to exec 'from xyz import *' in the global only namespace.
        """
        # From code.InteractiveInterpreter...

        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3
        # Check if this is a 'from xyz import *" statement.  If it is, then
        # execute it in the global namespace.  It will fail if it executes in
        # the local namespace.
        if import_all.match(source) is None:
            self.runcode(code)
        else:
            self.runcode_global(code)
        return False


    def runcode(self, code):
        """ Execute a code object in the given context.

            This is overloaded from the base class so that we can
            execute in both a global and a local context.  We are using a
            "dictionary-like" object for the locals.  The exec statement
            requires that the globals is a dict.

            The rest of the code is cut/pasted from the base class.
        """
        try:
            # Use both a global and local context.  This is the only change.
            exec code in self.globals, self.locals
        except SystemExit:
            raise
        except:
            self.showtraceback()
        else:
            if softspace(sys.stdout, 0):
                print


    ############################################################################
    # GlobalAndLocalInterpreter interface
    ############################################################################

    def runcode_global(self, code):
        """ Execute a code object in *only* the global context.

            This method makes it possible to run "from xyz import *" from
            the command line.  This isn't allowed if a non-dictionary local
            namespace is used.  Note that this method will not work if
            the global dictionary
        """
        try:
            # Use only the globals namespace for execution.
            exec code in self.globals
        except SystemExit:
            raise
        except:
            self.showtraceback()
        else:
            if softspace(sys.stdout, 0):
                print

    def runsource_global(self, source, filename="<input>", symbol="single"):
        """Compile/run source in interpreter using *only* the global namespace.

        Arguments are as for compile_command().

        One several things can happen:

        1) The input is incorrect; compile_command() raised an
        exception (SyntaxError or OverflowError).  A syntax traceback
        will be printed by calling the showsyntaxerror() method.

        2) The input is incomplete, and more input is required;
        compile_command() returned None.  Nothing happens.

        3) The input is complete; compile_command() returned a code
        object.  The code is executed by calling self.runcode() (which
        also handles run-time exceptions, except for SystemExit).

        The return value is True in case 2, False in the other cases (unless
        an exception is raised).  The return value can be used to
        decide whether to use sys.ps1 or sys.ps2 to prompt the next
        line.

        """
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3
        self.runcode_global(code)
        return False
