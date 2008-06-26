#-------------------------------------------------------------------------------
#
#  Traits editor for displaying a Python shell using a NumericContext for its
#  dictionary.
#
#  Written by: David C. Morrill
#
#  Date: 02/15/2007
#
#  (c) Copyright 2007 by Enthought, Inc.
#
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

# ETS imports
from enthought.traits.api import Str, Any
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.wx.basic_editor_factory import BasicEditorFactory

# App imports
from enthought.contexts.shell.context_shell import ContextPythonShell

#-------------------------------------------------------------------------------
#  '_ContextShellEditor' class:
#-------------------------------------------------------------------------------

class _ContextShellEditor ( Editor ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

     # Indicate that the plot editor is scrollable (default override):
    scrollable = True

    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------

    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self._shell  = ContextPythonShell( parent,
                                           block_unit = self.factory.block_unit )
        self.control = self._shell.control
        if self.factory.execute != '':
            self._shell.on_trait_change( self._do_execute, 'command_executed',
                                         dispatch = 'ui' )
            self._do_execute()

    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------

    def update_editor ( self ):
        """ Updates the editor when the object trait changes external to the
            editor.
        """
        self._shell.context = self.value

    #---------------------------------------------------------------------------
    #  Handles a shell editor command being executed:
    #---------------------------------------------------------------------------

    def _do_execute ( self ):
        setattr( self.object, self.factory.execute, self.control )

    #---------------------------------------------------------------------------
    #  Disposes of the contents of an editor:
    #---------------------------------------------------------------------------

    def dispose ( self ):
        """ Disposes of the contents of an editor.
        """
        super( _ContextShellEditor, self ).dispose()

        if self.factory is not None and self.factory.execute != '':
            self._shell.on_trait_change( self._do_execute, 'command_executed',
                                         remove = True )

#-------------------------------------------------------------------------------
#  'ContextShellEditor' class:
#-------------------------------------------------------------------------------

class ContextShellEditor ( BasicEditorFactory ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # Class used to create all editor styles (override):
    klass = _ContextShellEditor

    # Name of the [object.]trait to update when a command is executed:
    execute = Str

    # Optional block_unit
    block_unit = Any


if __name__ == "__main__":
    from enthought.traits.api import HasTraits
    from enthought.traits.ui.api import View, Item, Group
    from enthought.contexts.multi_context import MultiContext

    class ContextWrapper(HasTraits):
        context = MultiContext({"a":100, "b":200, "c":50})
        editor = ContextShellEditor()
        traits_view = View(Group(Item('context', editor=editor, width=400,
                                      height=400)))

    ContextWrapper().configure_traits()
