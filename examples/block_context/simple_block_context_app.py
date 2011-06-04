"""Simple Block Context Application

This application demonstrates the use of the Block-Context-Execution Manager
pattern, together with using a TraitslikeContextWrapper to make items inside a
data context appear like traits so that they can be used in a TraitsUI app.
"""
from traits.api import HasTraits, Instance, Property, Float, \
    on_trait_change, cached_property
from traitsui.api import View, Group, Item

from codetools.contexts.api import DataContext, TraitslikeContextWrapper
from codetools.contexts.items_modified_event import ItemsModified
from codetools.blocks.api import Block

code = """# my calculations
velocity = distance/time
momentum = mass*velocity
"""

class SimpleBlockContextApp(HasTraits):
    # the data context we are listening to
    data = Instance(DataContext)

    # the block we are executing
    block = Instance(Block)

    # a wrapper around the data to interface with the UI
    tcw = Property(Instance(TraitslikeContextWrapper), depends_on=["block", "data"])

    # a view for the wrapper
    tcw_view = Property(Instance(View), depends_on="block")

    @on_trait_change('data.items_modified')
    def data_items_modified(self, event):
        """Execute the block if the inputs in the data change"""
        if isinstance(event, ItemsModified):
            changed = set(event.added + event.modified + event.removed)
            inputs = changed & self.block.inputs
            if inputs:
                self.execute(inputs)

    @cached_property
    def _get_tcw_view(self):
        """Getter for tcw_view: returns View of block inputs and outputs"""
        inputs = tuple(Item(name=input)
                       for input in sorted(self.block.inputs))
        outputs = tuple(Item(name=output, style="readonly")
                        for output in sorted(self.block.outputs))
        return View(Group(*(inputs+outputs)),
                    kind="live")

    @cached_property
    def _get_tcw(self):
        """Getter for tcw: returns traits-like wrapper for data context"""
        in_vars = dict((input, Float) for input in self.block.inputs)
        out_vars = tuple(self.block.outputs)
        tcw = TraitslikeContextWrapper(_context=self.data)
        tcw.add_traits(*out_vars, **in_vars)
        return tcw

    def execute(self, inputs):
        """Restrict the code block to inputs and execute"""
        # only execute if we have all inputs
        if self.block.inputs.issubset(set(self.data.keys())):
            try:
                self.block.restrict(inputs=inputs).execute(self.data)
            except:
                # ignore exceptions in the block
                pass

if __name__ == "__main__":
    block = Block(code)
    data = DataContext(subcontext=dict(distance=10.0, time=2.5, mass=3.0))
    execution_manager = SimpleBlockContextApp(block=block, data=data)
    execution_manager.tcw.configure_traits(view=execution_manager.tcw_view)
