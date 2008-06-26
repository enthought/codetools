# Numeric libary imports
from numpy import ndarray

from enthought.traits.api import Dict

# Local imports
from unit_manipulation_adapter import UnitManipulationAdapter
from unit_converter_functions import array_to_unit_array_converter


unit_apply_converters = {ndarray: array_to_unit_array_converter}

class UnitApplyAdapter(UnitManipulationAdapter):
    """ Adapter that adds units to objects that do not have units.  The
        units used are chosen based on the name used for the object in
        the context.

        Note: This is an extremely thin wrapper around UnitManipulationAdapter.
              It only overrides the default settings for converters.
    """
    # override with a set of converters that add units to objects
    converters = Dict(unit_apply_converters)