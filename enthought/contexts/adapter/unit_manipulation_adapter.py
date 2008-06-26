""" Primary adapter implementation for many unit manipulation tasks
    such as conversion, correcting units, or adding units to an item.

    See unit_conversion_adapter.py for a concrete example.
"""

#Enthought Library imports
from enthought.traits.api import Dict, Any, implements, HasTraits

# Local imports
from i_adapter import IAdapter



class ConversionError(Exception):
    """ Raised if conversion fails for some reason.
    """
    pass


class UnitManipulationAdapter(HasTraits):
    """ Bi-directional unit conversion of values.

        This adapter converts values to a different unit system based on their
        name.  There is a name->units mapper for getitem conversions and a
        separate name->units adapter for setitem conversions so that
        read/write can result in different unit conversions.  This is useful
        when, for example, you want a context to preserve its current units
        for all its variables, but something using this context ( a shell or
        plot, or whatever) wants the values in another unit system.

        If units aren't found for a particular name, the converter silently
        lets the variable pass through.  If units are found, but a converter
        isn't, or the converter fails, a ConversionError is raised.  Users
        can pass in a dictionary of converters functions to be used for
        unit conversion.

        fixme: I can imagine places where we don't want name lookup to silently
               pass.  A flag like 'fail_on_name_not_found' or something like
               that might be useful.

    """

    implements(IAdapter)

    ############################################################################
    # UnitConversionContextAdapter traits
    ############################################################################

    # Mapping of names to their units when adapt_getitem is called.
    # It does not have to be dictionaries, but they must have a dictionary-like
    # get() method.
    # fixme: Define an interface for this...
    getitem_units = Any(dict())

    # Mapping of names to their units when adapt_getitem is called.
    # It does not have to be dictionaries, but they must have a dictionary-like
    # get() method.
    # fixme: Define an interface for this...
    setitem_units = Any(dict())

    # A type to converter mapping. The key is a data type and the value is
    # a function to convert that data type to new units:
    #     (data_type, func(value, new_units))
    converters = Dict()

    ############################################################################
    # Public IAdapter interface.
    ############################################################################

    def adapt_getitem(self, context, name, value):
        """ Convert 'value' to the desired units for objects of the given 'name'

            The getitem_units name->units mapper is used to look up the proper
            units.  If no units are found for 'name', the value passes through
            unaltered.  If a units are found, but an appropriate converter is
            not, or the conversion fails, a ConversionError is raised.
        """

        # Find the desired units (if specified) for the object.
        new_units = self.getitem_units.get(name, None)

        # Convert to the new units.
        if new_units:
            value = self._convert(value, new_units)

        return name, value

    def adapt_setitem(self, context, name, value):
        """ Convert 'value' to the desired units for objects of the given 'name'

            The setitem_units name->units mapper is used to look up the proper
            units.  If no units are found for 'name', the value passes through
            unaltered.  If a units are found, but an appropriate converter is
            not, or the conversion fails, a ConversionError is raised.
        """
        # Look up the units based on the variable name.
        new_units = self.setitem_units.get(name, None)

        # Convert object to new unit system if one is found.
        if new_units:
            value = self._convert(value, new_units)

        return name, value

    ############################################################################
    # UnitConversionContextAdapter interface.
    ############################################################################

    ### Private interface ######################################################

    def _convert(self, value, new_units):
        """ Find a converter for value and convert it to new_units.

            If no converter is found for the type, raise ConversionError
        """

        # Look up the converter for this data type from our conversion dict.
        converter = self.converters.get(type(value), None)

        if converter is not None:
            # Convert the value.
            value = converter(value, new_units)
        else:
            # Conversion requested (new_units exist), but a converter
            # wasn't found.
            msg = "Unable to find converter for type %s" % type(value)
            raise ConversionError, msg

        return value


