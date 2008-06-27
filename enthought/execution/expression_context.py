# Global imports
from UserDict import DictMixin

# Enthought library imports
from enthought.traits.api import implements, Str, Dict, Any, List, Instance, on_trait_change

# Block Canvas imports
from enthought.blocks.api import Block
from enthought.block_canvas.context.data_context import ListenableMixin, PersistableMixin, DataContext
from enthought.block_canvas.context.i_context import IContext, IListenableContext, ICheckpointable, \
                                                     IPersistableContext
from enthought.block_canvas.context.items_modified_event import ItemsModified

class ExpressionContext(ListenableMixin, PersistableMixin, DictMixin):
    """Provide a context wrapper that adds the ability to request expressions on variables
    in the underlying context, and re-evaluate those expressions and fire events when the
    underlying dependencies of the variables in the expression changes"""
    # FIXME: ICheckpointable would be nice
    implements(IListenableContext, IPersistableContext)

    name = Str('ExpressionContext')

    # The underlying context which contains variables
    # From which the expressions are calculated.
    underlying_context = Instance(IListenableContext)

    # The currently evaluated expressions, mapped to their last cached value.  None means
    # that the value is not cached.
    _expressions = Dict(Str, Any)
    # A list of variable dependencies for each expression
    _dependencies = Dict(Str, List(Str))

    def __init__(self, underlying_context, **traits):
        super(ExpressionContext, self).__init__(underlying_context=underlying_context)

    def __delitem__(self, key):
        """Delete an item from the ExpressionContext -- either in the underlying context,
        or if an already cached expression, delete it."""
        # if item is an expression, delete it from the list of dependencies, otherwise pass it down
        # to underlying
        if key in self._expressions:
            self._expressions.remove(key)
            for dep in list(Block(key).inputs):
                self._dependencies[dep].remove(key)
        else:
            del self.underlying_context[key]

    def __contains__(self, key):
        # FIXME: not sure what to do here -- maybe eval the expression in the context
        # and see if it works as an expression on this context if it's not in the underly
        # -ing
        return key in self.underlying_context
    
    def __getitem__(self, key):
        if key in self.underlying_context.keys():
            return self.underlying_context[key]
        else:
            try:
                # FIXME imports need to be more configurable
                # FIXME we may want to have cache rules on sizes so that we
                # don't keep around huge values that aren't needed anymore
                # however, there is a time/space tradeoff that really should be
                # used.  We currently support del so that is available if the user
                # wants to manually manage this.
                eval_globals = {}
                for lib in (__builtins__, __import__('numpy')):
                    for sym in dir(lib):
                        if not key.startswith('__'):
                            eval_globals[sym] = getattr(lib, sym)

                result = eval(key, eval_globals, self.underlying_context)
                self._expressions[key] = result
                for dep in Block(key).inputs:
                    self._dependencies.setdefault(dep, list())
                    self._dependencies[dep].append(key)
                return result
            except:
                return None

    def __setitem__(self, key, value):
        """We don't allow setting an expression per se, so it passes through
        to the underlying context.  Hopefully this won't be a problem in the
        future due to plots or other listeners trying to change values.
        Theoretically one could store the inverse of a function and allow this
        if the function was invertable"""
        
        self.underlying_context[key] = value
        return
    
    get = DictMixin.get

    def __str__(self):
        underlying_str = str(underlying_context)
        return '%s(%s)' % type(self).__name__, underlying_str

    @on_trait_change('underlying_context:items_modified')
    def _underlying_context_items_modifed(self, event):
        new_event = ItemsModified(context=self,
                                  added=[x for x in event.added],
                                  removed=[x for x in event.removed],
                                  modified=[x for x in event.modified])
        for event_list in (new_event.added, new_event.modified, new_event.removed):
            for item in event_list:
                if item in self._dependencies.keys():
                    for dep_item in self._dependencies[item]:
                        if dep_item not in event_list:
                            event_list.append(dep_item)
                        # Remove the cached value for the item
                self._expressions[item] = None
        self.items_modified = new_event
        return

    def _underlying_context_changed(self):
        self._expressions = {}
        self._dependencies = {}
        return
        
