import warnings
warnings.warn("""This location is deprecated.  Please update source file: enthought.contexts --> enthought.contexts""", DeprecationWarning) 
from adapted_data_context import AdaptedDataContext
from data_context import DataContext, ListenableMixin, PersistableMixin
from function_filter_context import FunctionFilterContext
from geo_context import GeoContext
from i_context import (IContext, IListenableContext, IRestrictedContext,
    IPersistableContext, ICheckpointable)
from multi_context import MultiContext
from traitslike_context_wrapper import TraitslikeContextWrapper

# fix me: should these be here?
from adapter.i_adapter import IAdapter
from adapter.masking_adapter import MaskingAdapter
from adapter.unit_apply_adapter import UnitApplyAdapter
from adapter.unit_conversion_adapter import UnitConversionAdapter
from adapter.unit_corrector_adapter import UnitCorrectorAdapter
from adapter.unit_manipulation_adapter import UnitManipulationAdapter
from adapter.name_adapter import NameAdapter
