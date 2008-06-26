# ETS library imports
from enthought.numerical_modeling.units.api import UnitArray
from enthought.traits.api import Dict

# Local imports
from unit_manipulation_adapter import UnitManipulationAdapter
from unit_converter_functions import  unit_array_units_overwriter


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




