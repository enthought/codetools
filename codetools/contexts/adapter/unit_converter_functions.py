#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#

""" A collection of unit manipulation functions that are used as converters
    for UnitManipulationAdapter instantiations.

    See unit_manipulation_adapter_factories.py for concrete examples of how
    they are used.
"""

from __future__ import absolute_import

import numpy

# ETS
from scimath import units
from scimath.units.api import UnitArray


################################################################################
# Unit Converter functions:
#
# These functions do unit conversion on objects with units to the same type
# of object with new units.
################################################################################

def unit_array_units_converter(unit_array, new_units):
    """ Convert a UnitArray from one set of units to another.
    """
    if unit_array.units != new_units:
        # A conversion is needed. Must pass in a real ndarray instead of
        # a UnitArray since operations on it will also try to conversions that
        # we don't want it to do.
        result = units.convert(unit_array.view(numpy.ndarray), unit_array.units,
            new_units).view(UnitArray)
        result.units = new_units
    else:
        # No conversion needed.  Just return the unit_array.
        result = unit_array

    return result


################################################################################
# Unit 'Setter' functions.
#
# These functions don't really do unit conversion as much as the add units to
# objects that don't have them.  This often involves converting them to
# a new type of object.
################################################################################

def array_to_unit_array_converter(array, new_units):
    """ Create a UnitArray with units='new_units' from the given 'array'.
    """

    return UnitArray(array, units=new_units)


################################################################################
# Unit 'Correcter' functions.
#
# These functions *overwrite* the existing units on an object with new units.
# No conversion unit conversion takes place.
################################################################################

def unit_array_units_overwriter(unit_array, new_units):
    """ Overwrite the units for a UnitArray with the new units.
    """

    if unit_array.units != new_units:
        unit_array.units = new_units

    return unit_array

