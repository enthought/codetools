""" Create a shell that can interact with a NumericContext.
"""

# wx imports:
import wx

# Enthought Library imports:
from enthought.numerical_modeling.numeric_context.api import NumericContext
from enthought.pyface.python_shell import PythonShell
from enthought.pyface.ui.wx.python_shell import PyShell #temporary
#from enthought.pyface.ui.qt4.python_shell import PyShell #temporary
from enthought.traits.api import Instance, Property, Any
from enthought.util.wx.drag_and_drop import PythonDropTarget

# Local imports:
from global_and_local_interpreter import GlobalAndLocalInterpreter


class ContextPythonShell ( PythonShell ):

    ############################################################################
    # ContextPythonShell traits.
    ############################################################################

    # An optional BlockUnit class so the shell can have the block unit update
    # its variable list when the context is modfied in this way
    block_unit = Any

    # An evaluation_context that is used as the locals namespace for evaluation.
    context = Any # Instance(ANumericContext, ())


    ############################################################################
    # PythonShell interface.
    ############################################################################

    ### trait listeners ########################################################

    def _command_executed_changed(self):
        """ Make sure that the block unit's variable list gets updated when
            a command is executed.
        """
        if self.block_unit is not None:
            self.block_unit.variables.update_variables()

    ### private interface ######################################################

    def _create_control ( self, parent ):
        """ Creates the toolkit-specific control for the widget. """


        # changed the way this method was created.
        # fixme: We probably should refactor this in the pyface class so that
        #        we don't have to overload this entire method for this change.
        shell = PyShell( parent, -1, locals = self.context,
                         InterpClass = GlobalAndLocalInterpreter )

        # Listen for key press events.
        wx.EVT_CHAR( shell, self._wx_on_char )

        # Enable the shell as a drag and drop target.
        shell.SetDropTarget( PythonDropTarget( self ) )

        return shell

    def _context_default ( self ):
        return NumericContext()

    def _context_changed ( self, context ):
        if self.control is not None:
            self.control.interp.locals = context
        if self.block_unit is not None:
            self.block_unit.variables.update_variables()