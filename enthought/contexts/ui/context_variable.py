""" View models for viewing and editing contexts in a table.
"""

import numpy

from enthought.pyface.timer.api import do_later
from enthought.traits.api import (Any, Bool, Event, HasTraits, Instance, List,
    Property, Str, TraitError, Undefined, on_trait_change)
import enthought.traits.ui.api as tui
from enthought.traits.protocols.api import AdaptationFailure, adapt
from enthought.traits.ui.menu import OKCancelButtons

from enthought.contexts.api import (DataContext, IContext,
    IListenableContext)
from enthought.block_canvas.interactor.editors import array_eval_editor
from enthought.block_canvas.app.utils import regex_from_str


def set_var_value(value):
    """ Setting values in a BlockVariable to be either None, an int, a float,
    a string, or a numpy array.
        
    A few common cases for numpy expressions are checked like 'array', 'arange',
    'linspace', 'zeros', and 'ones' and anything 'numpy.foo()'.

    Parameters:
    -----------
    value : Str

    Returns
    -------
    obj : object
        Undefined if we cannot parse this at all. Recipients should check for
        this value and raise an error to force the Traits UI Editor to do
        something appropriate. The empty string will evaluate to None.

    Examples
    --------
    >>> from enthought.contexts.ui.context_variable import set_var_value
    >>> set_var_value('') is None
    True
    >>> set_var_value('None') is None
    True
    >>> set_var_value('1')
    1
    >>> set_var_value('10.0')
    10.0
    >>> set_var_value('numpy.array([1,2,3])')
    array([1, 2, 3])
    >>> set_var_value('array([1,2,3])')
    array([1, 2, 3])
    >>> set_var_value('arange(5)')
    array([0, 1, 2, 3, 4])
    >>> set_var_value('linspace(0,1,6)')
    array([ 0. ,  0.2,  0.4,  0.6,  0.8,  1. ])
    >>> set_var_value('zeros([3])')
    array([ 0.,  0.,  0.])
    >>> set_var_value('ones([3])')
    array([ 1.,  1.,  1.])
    >>> set_var_value('"a string"')
    'a string'
    >>> set_var_value('nothing we can evaluate')
    <undefined>
    """

    str_value = str(value).strip()
    if str_value == '' or str_value == 'None':
        return None
    else :
        new_value = None
        for val_type in [int, float]:
            try:
                new_value = val_type(str_value)
                break
            except ValueError:
                pass

        namespace = dict(
            numpy = numpy,
            arange = numpy.arange,
            array = numpy.array,
            linspace = numpy.linspace,
            zeros = numpy.zeros,
            ones = numpy.ones,
        )
        if new_value is None:
            try:
                new_value = eval(str_value, namespace)
            except Exception, e:
                # Could not evaluate the expression. Return Undefined and let
                # the Traits mechanisms handle it. We cannot pass up the
                # exception because it will simply be ignored in TextEditor.
                new_value = Undefined

    return new_value



class ContextVariable(HasTraits):
    """ Represent a single row in the table.
    """

    # Describe the variable itself.
    name = Str()
    type = Str()
    value = Any()

    # Work around the "edit" icon for values which can be edited inline. Fake
    # this value as False if the inline editor can be used.
    editable = Property(Bool())


    def get_editor(self):
        """ Dispatch an appropriate Traits UI editor for the value by its type.
        """
        editor = tui.TextEditor(
            format_func=repr,
            evaluate=set_var_value,
            auto_set=False,
            enter_set=True,
        )
        if isinstance(self.value, numpy.ndarray):
            editor = array_eval_editor
        
        return editor

    def trait_view(self, name=None, view_element=None):
        """ Defines the view dynamically. 
        """
        return tui.View(
            tui.Item('value',
                     editor=self.get_editor(),
                     show_label=False),
            buttons=OKCancelButtons,
            resizable=True,
            title="Edit '" + self.name + "'",
        )

    def __getitem__(self, index):
        """ Fake a length-3 sequence interface to implement our desired sort
        order.

            object[0] = name
            object[1] = None;   instead of value; in order to avoid sorting by
                                value; which gives errors when arrays are
                                sorted.
            object[2] = None;   instead of type
        """
        if index == 0:
            return self.name
        else:
            return None

    def __repr__(self):
        return '%s(name=%r, type=%r, value=%r)' % (self.__class__.__name__, self.name, self.type, self.value)


    #### Traits stuff ##########################################################

    def _get_editable(self):
        """ Work around the "edit" icon for values which can be edited inline.
        Fake this value as False if the inline editor can be used.
        """ 
        if self.value is None or isinstance(self.value, (int, float, basestring)):
            return False
        return True

    def _value_default(self):
        return 1.0

    def _value_changed(self, new):
        """ Detect if we are being assigned Undefined from the TextEditor's
        evaluation function.

        In that case raise a TraitError. This will tell the TextEditor to
        display an error message.
        """
        if new is Undefined:
            raise TraitError("could not evaluate input")


class ContextVariableList(HasTraits):
    """ View model for a list of ContextVariables from an IContext.
    """

    # The context to be viewed.
    context = Instance(IListenableContext, factory=DataContext, adapt='yes',
        rich_compare=False)

    # One ContextVariable for each name in the context.
    variables = List(Any())

    # The current search term.
    search_term = Str()

    # The search results, a subset of `variables`.
    search_results = List(Any())

    # The currently selected rows for listening.
    table_selection = List(ContextVariable)

    # Tell listeners to re-execute for the given set of names.
    execute_for_names = Event()

    # Tell listeners to delete the given names.
    delete_names = Event()


    def __init__(self, **traits):
        super(ContextVariableList, self).__init__(**traits)
        # Be sure to read the context on initialization.
        self.update_variables()


    #### Traits stuff ##########################################################

    def trait_view(self, name=None, view_items=None):
        from context_variable_ui import context_variables_view
        return context_variables_view(self)

    @on_trait_change('context:items_modified')
    def context_items_modified(self, event):
        """ Propagate changes from the context to the list.
        """
        cvs = {}
        for cv in self.variables:
            cvs[cv.name] = cv

        newvariables = list(self.variables)

        for name in event.removed:
            if name in cvs:
                # It might already be deleted if the deletion came from the UI.
                newvariables.remove(cvs[name])

        for name in event.modified:
            if name in cvs:
                cvs[name].value = self.context[name]

        self._extract_variables_from_context(self.context, event.added)

        self.variables = newvariables

    @on_trait_change('search_term,variables')
    def _update_search_results(self):
        """ Update the search results when the the search term changes.
        """
        # XXX: this is getting called far too often.
        items = []
        for filter in regex_from_str(self.search_term):
            items.extend( item for item in self.variables
                          if filter.match( item.name ) is not None )
        items.sort(key=lambda x: x.name)
        self.search_results = items

    @on_trait_change('search_results:value')
    def _item_value_changed(self, obj, name, new):
        """ Update the context when a variable's value is changed in the table.
        """
        if name == 'value':
            name = str(obj.name)
            self.context[name] = obj.value

    def _search_results_items_changed(self, event):
        """ Add/remove the items from the context. 

        This should only get called when the user adds or deletes a row from the
        GUI. Changing the search term does not affect this.
        
        Unique names are enforced. The enforcement is done here because the
        variables are constructed before being put on the list so this is the
        first opportunity to check with the context.
        """
        # XXX: use the undo framework for this.

        self.context.defer_events = True
        
        for var in event.added:
            var.name = self._create_unique_key(var.name)
            self.context[var.name] = var.value

        for var in event.removed:
            del self.context[var.name]
            
        # This may have been triggered by creating a new var with the UI,
        # in which case, adding the new row needs to finish before we handle
        # the context events.
        
        def _enable_events(context):
            context.defer_events = False
            
        do_later(_enable_events, self.context)


    #### Public interface ######################################################

    @on_trait_change('context')
    def update_variables(self):
        """ Populate variables from the context.
        """
        self.variables = []

        if self.context is not None:
            variables = self._extract_variables_from_context(self.context)

        self.variables = [var for var in self.variables if var.value != '']
        
        self._update_search_results()


    #### Private interface #####################################################

    def _extract_variables_from_context(self, context, names=None):
        """ Populate variables from the context.

        Parameters:
        -----------
        context: IContext
        names : list of str, optional
            The list of names to extract. If not provided, then all of the keys
            will be extracted.
        """

        variables = []
        if names is None:
            names = context.keys()
        for key in names:
            value = context[key]
            # new_var will be a list in order to handle subcontexts.
            new_var = self._create_variable(key, value)
            if new_var is not None:
                variables.extend(new_var)

        # Look for these variables in our pre-existing list.
        for key, value, datatype in variables:
            found = False
            for i in range(len(self.variables)):
                if not found and self.variables[i].name == key:
                    self.variables[i].value = value
                    found = True
            if not found:
                var = ContextVariable(
                    name = key,
                    type = 'unbound_input',
                    value = value,
                )
                self.variables.append(var)

    def _create_variable(self, key, value):
        """ Create variables from key, value applied here.

        Parameters:
        -----------
        key : Str
        value : Float/Str/Array/IContext

        Returns:
        --------
        result: List(Tuple)
            tuple is ordered as (key, value, datatype)
        """
 
        if isinstance(value, int) or isinstance(value, float):
            return [(key, value, 'scalar')]

        if isinstance(value, basestring):
            return [(key, value, 'str')]

        if isinstance(value, numpy.ndarray):
            return [(key, value, 'array')]

        try:
            value = adapt(value, IContext)
            variables = []
            for sub_key in value.keys():
                sub_value = value[sub_key]
                sub_key = "%s[%r]" % (key, sub_key)
                variable_list = self._create_variable(sub_key, sub_value)
                if variable_list:
                    variables += variable_list
            return variables
        except AdaptationFailure:
            pass

        return None

    def _create_unique_key(self, desired_name):
        """ Creates a unique name by appending _x to the desired name.
        
        The algorithm here could use some refinement, but I expect only minimal
        name collisions as the result of operations of the ContextVariableList.
        Collisions are much more likely to happen due to the block execution.
        """
        desired_name = str(desired_name)
        if not desired_name in self.context:
            return desired_name

        desired_name += "_"
        index = 1
        test_name = desired_name + str(index)
        while self.context.has_key(test_name):
            index += 1
            test_name = desired_name + str(index)

        return test_name


if __name__ == '__main__':
    import pprint
    from enthought.contexts.api import DataContext
    from context_variable_ui import context_variables_view

    dc = DataContext()
    dc['foo_int'] = 1
    dc['foo_float'] = 1.5
    dc['foo_array'] = numpy.arange(10)
    dc['foo_str'] = 'a string'
    dc['bar_int'] = 2
    dc['bar_float'] = 2.5
    
    cvl = ContextVariableList(context=dc)
    cvl.configure_traits(view=context_variables_view)

    pprint.pprint(dc.subcontext)
