#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#

from __future__ import absolute_import

# ETS library imports
from scimath.units.api import UnitArray
from traits.api import Dict

# Local imports
from .unit_manipulation_adapter import UnitManipulationAdapter
from .unit_converter_functions import  unit_array_units_overwriter


unit_corrector_converters =  {UnitArray: unit_array_units_overwriter}

class UnitCorrectorAdapter(UnitManipulationAdapter):
    """ Overwrite units on an object with a new set of units.  The new units
        are found based on the name for the object in the context.

        Note: This is an extremely thin wrapper around UnitManipulationAdapter.
              It only overrides the default settings for converters.

        fixme: We may want to modify converters so that they don't overwrite
               compatible units with new units.  We may only want to correct
               untis that are completely screwed up...
    """
    # override with a set of converters that add units to objects
    converters = Dict(unit_corrector_converters)




