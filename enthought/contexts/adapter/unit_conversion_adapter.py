""" Experimental adapter that, given a context, adapts it to a particular set
    of units.

    For example, say you have a context with logs that have unknown units, and
    you want to ensure logs that you use are of a specific set.  Below, we have
    a log 'depth' in meters that we want to ensure is in 'feet'.  The adapter
    enforces this.

    >>> from enthought.units.length import meters, feet
    >>> from enthought.numerical_modeling.units.api import UnitArray
    >>> from enthought.contexts.api import AdaptedDataContext, DataContext
    >>> from enthought.contexts.api import UnitConversionAdapter
    >>> old_log = UnitArray((1,2,3),units=meters)
    >>> context=AdaptedDataContext(context=DataContext())
    >>> context['depth'] = old_log
    >>> getitem_units = {'depth':feet}
    >>> adapter = UnitConversionAdapter(getitem_units=getitem_units)
    >>> context.push_adapter(adapter)
    >>> new_log = context['depth']
    >>> print new_log.units
    0.3048*m
    >>> print new_log
    [ 3.2808399   6.56167979  9.84251969]

    Note that currently , get and set both convert to the same unit system.
    This is quite possibly not what we want to happen.  You want gets in one
    units system and sets in another.

    Also Note that by using this adapter approach with multiple adapter layers,
    we potentially have a serious performance impact.  Imagine having multiple
    unit conversion adapters chained together.  Each of these would convert the
    data to new units individually resulting in a large number of new log
    creations and calculation steps.  It would be much better to "reduce" these
    conversions by multiplying them together and then apply the conversion once
    to the entire array.  The desire to do this may lead to an alternative
    architecture where we have a list of "converters" or adapters that are
    attached to a GeoContext that are used when dealing with array conversions.
    This would allow some external object to examine all of them at once and
    them make intelligent decisions about how to optimize their application.
"""

# Numeric libary imports
from numpy import ndarray

# ETS library imports
from enthought.numerical_modeling.units.api import UnitArray
from enthought.traits.api import Dict

# Local imports
from unit_manipulation_adapter import UnitManipulationAdapter
from unit_converter_functions import (array_to_unit_array_converter,
                                      unit_array_units_converter,
                                      unit_array_units_overwriter)

conversion_converters = {UnitArray: unit_array_units_converter}

class UnitConversionAdapter(UnitManipulationAdapter):
    """

        Note: This is an extremely thin wrapper around UnitManipulationAdapter.
              It only overrides the default settings for converters.
    """
    # override with a set of converters customized for unit conversion.
    converters = Dict(conversion_converters)





