import numpy

from enthought.traits.ui.table_column import ObjectColumn
from enthought.traits.ui import api as tui
from enthought.traits.ui.extras.api import EditColumn, CheckboxColumn
from enthought.traits.ui import menu
from enthought.traits.ui.wx.constants import WindowColor

from enthought.block_canvas.ui.search_editor import SearchEditor
from enthought.block_canvas.interactor.interactor_config import (InteractorConfig,
        VariableConfig)
from enthought.block_canvas.interactor.configurable_interactor import ConfigurableInteractor

from context_variable import ContextVariable


class ContextVariableColumn(ObjectColumn):
    """ A column declaration for the variable value.
    """

    def get_editor(self, object):
        return object.get_editor()

    def is_editable(self, object):
        """ Return True if the value column is editable.
        """
        if object.value is None or isinstance(object.value, (int, float, basestring)):
            return True
        return False

    def get_cell_color(self, object):
        """ Since we are spoofing the editability, we need to override this to
        avoid the "read-only" cell color.
        """
        return self.cell_color_

    def get_value(self, object):
        """ Get the string for display.
        """
        raw_value = self.get_raw_value(object)
        # Use the numpy print formatting to get a nice representation for arrays
        # which will fit in the table. Restore numpy's print options after we
        # are done.
        if isinstance(raw_value, numpy.ndarray):
            old_print_options = numpy.get_printoptions()
            try:
                numpy.set_printoptions(precision = 4, threshold = 3,
                                       edgeitems = 1, linewidth = 30,
                                       suppress = False)
                value = numpy.array2string(object.value)
            finally:
                if isinstance(old_print_options, tuple):
                    # An older version of numpy.
                    numpy.set_printoptions(*old_print_options)
                else:
                    # A recent version of numpy.
                    numpy.set_printoptions(**old_print_options)
            return value
        else:
            return repr(raw_value)


def context_variable_factory(*row_factory_args, **row_factory_kw):
    #create an empty var for an empty row
    return ContextVariable()


class CVLHandler(tui.Controller):
    """ Handler for ContextVariableList Traits UIs.
    """

    def _on_execute(self, selection):
        """ Inform the listeners that they should execute based on the selected
        variables.
        """
        names = [row.name for row in selection if row.name != '']
        self.model.execute_for_names = names

    def _on_delete(self, selection):
        """ Delete some rows.
        """
        names = [row.name for row in selection if row.name != '']
        self.model.delete_names = names

    def _on_interact(self, selection):
        """ Bring up a ConfigurableInteractor on the selected variables
        """
        try:
            from enthought.block_canvas.app import scripting
        except:
            return
        app = scripting.app
        exp = app.project.active_experiment

        # Set the shadow context on the experiment for the purposes
        # of this interacttor
        # FIXME: We need to put on a proper shadow context!
        exp.context.shadows = [exp._local_context]
    
        var_configs = [VariableConfig(name=row.name) for row in selection]
        config_interactor = InteractorConfig(vars=self.model.variables,
                                             var_configs=var_configs)
        ui = config_interactor.edit_traits(kind="modal")
        if ui.result:
            interactor = ConfigurableInteractor(context=exp.context,
                                block = exp.exec_model.block,
                                interactor_config = config_interactor)
            interactor.edit_traits(kind="livemodal")

        # FIXME: We need to put on a proper shadow context!
        # Remove the bogus .shadows trait
        #delattr(exp.context, "shadows")
        #print "removing shadow context"

def context_variables_view(model):
    """ Instantiate a Traits UI View for a ContextVariableList.
    """
    context_menu = menu.Menu(
        menu.ActionGroup(
            menu.Action(name='Execute for Selection', action='handler._on_execute(selection)'),
            menu.Action(name='Execute for All', action='handler._on_execute([])'),
        ),
        menu.ActionGroup(
            menu.Action(name='Delete', action='handler._on_delete(selection)'),
        ),
        menu.ActionGroup(
            menu.Action(name='Interact', action='handler._on_interact(selection)'),
        ),
    )

    view = tui.View(
        tui.Item( 'search_term',
            show_label = False,
            editor     = SearchEditor( text = "Search for variables" ),
        ),
        tui.Item( 'search_results',
            id         = 'search_results',
            show_label = False,
            editor = tui.TableEditor(
                columns = [
                    ObjectColumn(name='name', width=75),
                    ContextVariableColumn(name='value', width=75),
                    EditColumn(name='value', width=25)
                ],
                selected = 'table_selection',
                edit_on_first_click = False,
                auto_add = True,
                configurable = False,
                menu = context_menu,
                row_factory = context_variable_factory,
                sortable = False,
                sort_model = True,
                show_column_labels = False,
                selection_bg_color = 'light blue',
                selection_color = 'black',
                selection_mode = 'rows',
                label_bg_color = WindowColor,
                cell_bg_color = 0xFFFFFF,
                auto_size = False,
            ),
        ),
        id        = 'context_variables_view',
        resizable = True,
        handler   = CVLHandler(model=model),
    )
    return view

