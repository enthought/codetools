# Enthought library imports
from enthought.traits.api import Code, HasTraits, Instance, Str, Button
from enthought.traits.ui.api import View, Group, Item
from enthought.traits.ui.wx.constants import WindowColor

from enthought.chaco2.chaco2_plot_container_editor import PlotContainerEditor
from enthought.chaco2.api import PlotComponent, VPlotContainer
from enthought.chaco2.plot import Plot

from enthought.block_canvas.execution.api import ExpressionContext
from enthought.block_canvas.context.data_context import DataContext
from enthought.block_canvas.plot.plot_data_context_adapter import \
     PlotDataContextAdapter

class ExpressionContextDemo(HasTraits):
    code = Code()
    execute = Button()
    plots = Instance(PlotComponent)
    value_expression = Str('')
    index_expression = Str('')
    view_expression = Button()
    data_context = Instance(DataContext)
    expression_context = Instance(ExpressionContext)

    traits_view = View('code',
                       'execute',
                       Item('plots', editor=PlotContainerEditor()),
                       'value_expression',
                       'index_expression',
                       Item('view_expression', show_label=False),
                       resizable=True)


    def __init__(self):
        self.data_context = DataContext()
        self.expression_context = ExpressionContext(self.data_context)
        self.plots = VPlotContainer()
        return

    def _view_expression_fired(self):
        context_adapter = PlotDataContextAdapter(context=self.expression_context)
        
        plot = Plot(context_adapter)
        plot.plot((self.index_expression, self.value_expression))
        self.plots.add(plot)
        self.plots.request_redraw()
        return

    def _execute_fired(self):
        exec self.code in {}, self.data_context
        return
    
if __name__ == '__main__':
    ecd = ExpressionContextDemo()
    ecd.configure_traits()

    
