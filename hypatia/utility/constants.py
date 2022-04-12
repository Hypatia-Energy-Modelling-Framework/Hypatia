# -*- coding: utf-8 -*-
from enum import Enum

"""
This module returns the constants of the code inclduing the info of sets and
parameter filese
"""
from typing import TypedDict

global_set_ids = {
    "Regions": ["Region", "Region_name"],
    "Years": ["Year", "Year_name"],
    "Timesteps": ["Timeslice", "Timeslice_name", "Timeslice_fraction"],
    "Time_horizon": ["Start", "End"],
    "Carriers_glob": ["Carrier", "Carr_name", "Carr_type", "Carr_unit"],
    "Technologies_glob": ["Technology", "Tech_name", "Tech_category",
    "Tech_cap_unit", "Tech_act_unit"],
    "Emissions": ["Emission", "Emission_name", "Emission_unit"]
}


regional_set_ids = {
    "Technologies": ["Technology", "Tech_name", "Tech_category"],
    "Carriers": ["Carrier", "Carr_name", "Carr_type"],
    "Carrier_input": ["Technology", "Carrier_in"],
    "Carrier_output": ["Technology", "Carrier_out"],
}

technology_categories = [
    "Supply",
    "Conversion",
    "Conversion_plus",
    "Transmission",
    "Demand",
    "Storage",
]

carrier_types = ["Resource", "Intermediate", "Demand"]

class ModelMode(Enum):
    Planning = "Planning"
    Operation = "Operation"

class TopologyType(Enum):
    SingleNode = "SingleNone"
    MultiNode = "MultiNode"
