"""
Registry of the constraints Hypatia can add to a model.

Core constraints are always active (each one still decides by itself, through
its MODES / TOPOLOGY_TYPES / ENSURE_FEASIBILITY class attributes, whether it
applies to a given model).

Optional constraints are switched on per model, by name, through the
``optional_constraints`` argument of ``hypatia.Model``. Enabling one also
makes Hypatia create and read the parameter sheets that constraint needs.
"""
from typing import Iterable, List, Tuple

from hypatia.backend.constraints.Balance import Balance
from hypatia.backend.constraints.BalanceUnMetDemand import BalanceUnMetDemand
from hypatia.backend.constraints.TradeBalance import TradeBalance
from hypatia.backend.constraints.ResourceTechAvailability import ResourceTechAvailability
from hypatia.backend.constraints.TotalCapacityRegional import TotalCapacityRegional
from hypatia.backend.constraints.NewCapacityRegional import NewCapacityRegional
from hypatia.backend.constraints.TechEfficency import TechEfficency
from hypatia.backend.constraints.AnnualProductionRegional import AnnualProductionRegional
from hypatia.backend.constraints.EmissionCapRegional import EmissionCapRegional
from hypatia.backend.constraints.EmissionCapGlobal import EmissionCapGlobal
from hypatia.backend.constraints.EmissionConsumedRegional import EmissionConsumedRegional
from hypatia.backend.constraints.StorageMaxMinChange import StorageMaxMinChange
from hypatia.backend.constraints.StorageMaxFlowInOut import StorageMaxFlowInOut
from hypatia.backend.constraints.StorageCyclicBoundary import StorageCyclicBoundary
from hypatia.backend.constraints.LineTotalCapacity import LineTotalCapacity
from hypatia.backend.constraints.TotalCapacityGlobal import TotalCapacityGlobal
from hypatia.backend.constraints.NewCapacityGlobal import NewCapacityGlobal
from hypatia.backend.constraints.AnnualProductionGlobal import AnnualProductionGlobal
from hypatia.backend.constraints.LineAvailability import LineAvailability
from hypatia.backend.constraints.LineNewCapacity import LineNewCapacity
from hypatia.backend.constraints.LandUsageRegional import LandUsageRegional
from hypatia.backend.constraints.LandUsageGlobal import LandUsageGlobal
from hypatia.backend.constraints.RenewableProductionRegional import RenewableProductionRegional
from hypatia.backend.constraints.RenewableProductionGlobal import RenewableProductionGlobal
from hypatia.backend.constraints.NewCapacityNonneg import NewCapacityNonneg
from hypatia.backend.constraints.CHPOperatingRange import CHPOperatingRange
from hypatia.backend.constraints.ProductionRamp import ProductionRamp
from hypatia.backend.constraints.MinTechPowerOutput import MinTechPowerOutput
from hypatia.backend.constraints.ElectrolysisConsumption import ElectrolysisConsumption
from hypatia.backend.constraints.BooleanForStorage import BooleanForStorage


CORE_CONSTRAINTS = [
    Balance,
    BalanceUnMetDemand,
    TradeBalance,
    ResourceTechAvailability,
    TotalCapacityRegional,
    NewCapacityRegional,
    TechEfficency,
    AnnualProductionRegional,
    EmissionCapRegional,
    EmissionCapGlobal,
    EmissionConsumedRegional,
    StorageMaxMinChange,
    StorageMaxFlowInOut,
    StorageCyclicBoundary,
    LineTotalCapacity,
    TotalCapacityGlobal,
    NewCapacityGlobal,
    AnnualProductionGlobal,
    RenewableProductionGlobal,
    LineAvailability,
    LineNewCapacity,
    NewCapacityNonneg,
    RenewableProductionRegional,
    LandUsageRegional,
    LandUsageGlobal,
]

# Name used in Model(optional_constraints=[...]) -> constraint class.
# The order of this dict is the order in which enabled constraints are appended
# after the core ones, so the built problem does not depend on the order the
# user lists them in.
OPTIONAL_CONSTRAINTS = {
    # CHPs with a variable operating range (feasible operating region).
    "chp_operating_range": CHPOperatingRange,
    # Ramp-up/ramp-down limits. Not compatible with StorageCyclicBoundary as
    # currently formulated.
    "production_ramp": ProductionRamp,
    # Minimum power output when a technology runs. Big-M formulation: can cause
    # numerical issues.
    "min_tech_power_output": MinTechPowerOutput,
    # Electricity consumption of electrolysers. Requires a carrier named
    # exactly "Electricity".
    "electrolysis_consumption": ElectrolysisConsumption,
    # Binary variables preventing simultaneous charge and discharge of storage
    # (turns the problem into a MILP).
    "boolean_for_storage": BooleanForStorage,
}

# Kept for backward compatibility with code that imported CONSTRAINTS.
CONSTRAINTS = CORE_CONSTRAINTS


def resolve_optional_constraints(names: Iterable[str] = ()) -> Tuple[str, ...]:
    """Validate the requested optional constraint names.

    Names are case-insensitive and duplicates are ignored. Returns them in the
    canonical order of OPTIONAL_CONSTRAINTS. Raises ValueError on unknown names,
    listing the accepted ones, so a typo fails loudly instead of silently
    building a different model.
    """
    if names is None:
        return ()
    if isinstance(names, str):
        # A bare string would otherwise be iterated character by character.
        names = [names]

    requested = {str(name).strip().lower() for name in names}
    unknown = sorted(requested - OPTIONAL_CONSTRAINTS.keys())
    if unknown:
        raise ValueError(
            f"Unknown optional constraint(s): {unknown}. "
            f"Accepted names: {list(OPTIONAL_CONSTRAINTS)}"
        )
    return tuple(name for name in OPTIONAL_CONSTRAINTS if name in requested)


def active_constraints(optional_names: Iterable[str] = ()) -> List[type]:
    """Core constraints followed by the enabled optional ones."""
    return CORE_CONSTRAINTS + [
        OPTIONAL_CONSTRAINTS[name] for name in resolve_optional_constraints(optional_names)
    ]
