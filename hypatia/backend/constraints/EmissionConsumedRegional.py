from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import get_emission_types
import pandas as pd
import numpy as np
import cvxpy as cp

"""
Defines the maximum amount of CO2 that can be consumed from the captured CO2 amount
"""
class EmissionConsumedRegional(Constraint):
    def _check(self):
        assert hasattr(self.variables, "captured_emission_by_region"), "captured_emission_by_region must be defined"
        assert hasattr(self.variables, "used_emissions_by_region"), "used_emissions_by_region must be defined"
    
    def rules(self):
        rules = []
        
        for emission_type in get_emission_types(self.model_data.settings.global_settings):

            for reg in self.model_data.settings.regions:
                
                regional_emission_captured = np.zeros(
                    (len(self.model_data.settings.years), 1)
                )
                regional_emission_consumed = np.zeros(
                    (len(self.model_data.settings.years), 1)
                ) 
                for key, value in self.variables.captured_emission_by_region[reg][emission_type].items():
                    regional_emission_captured += cp.sum(value, axis=1)
                    
                for key, value in self.variables.used_emissions_by_region[reg][emission_type].items():
                    regional_emission_consumed += cp.sum(value, axis=1)
                    
                rules.append(regional_emission_captured - regional_emission_consumed >= 0)
                
        return rules                