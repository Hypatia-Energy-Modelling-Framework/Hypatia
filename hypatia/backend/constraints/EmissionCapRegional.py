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
Defines the CO2 emission cap within each region
"""
class EmissionCapRegional(Constraint):
    def _check(self):
        assert hasattr(self.variables, "emission_by_region"), "emission_by_region must be defined"
    
    def rules(self):
        rules = []
        
        for emission_type in get_emission_types(self.model_data.settings.global_settings):

            for reg in self.model_data.settings.regions:
                
                regional_emission = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps), 1)
                )
                for key, value in self.variables.emission_by_region[reg][emission_type].items():
                    regional_emission += cp.sum(value, axis=1)
                emission_cap = self.model_data.regional_parameters[reg]["emission_cap_annual"][
                    "{} Global Cap".format(emission_type)
                ].values
                emission_cap.shape = regional_emission.shape
                rules.append(emission_cap - regional_emission >= 0)
                
                emission_power = np.zeros((len(self.model_data.settings.years), 1))
                
                for key, value in self.variables.emission_by_region[reg][emission_type].items():
                    
                    for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):
            
                        for carr in self.variables.totalprodbycarrier[reg].keys():
                        
                            if carr != 'Electricity':
                                continue
                                
                            if (
                                carr
                                in self.model_data.settings.regional_settings[reg]["Carrier_output"]
                                .loc[
                                    self.model_data.settings.regional_settings[reg]["Carrier_output"]["Technology"]
                                    == tech
                                ]["Carrier_out"]
                                .values
                            ):
                                emission_power += self.variables.emission_by_region[reg][emission_type][key][:,indx]
                emission_power_cap = self.model_data.regional_parameters[reg]["emission_cap_annual_power"][
                    "{} Power Cap".format(emission_type)
                ].values
                emission_power_cap.shape = emission_power.shape
                rules.append(emission_power_cap - emission_power >= 0)

        return rules

    def _required_regional_parameters(settings):
        required_parameters = {}
        for reg in settings.regions:
            required_parameters[reg] = {
                "emission_cap_annual": {
                    "sheet_name": "Emission_cap_annual",
                    "value": 1e10,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": pd.Index(
                        [emission_type + " Global Cap" for emission_type in get_emission_types(
                            settings.global_settings
                        )]
                    ),
                },
                "emission_cap_annual_power": {
                    "sheet_name": "Emission_cap_annual_power",
                    "value": 1e10,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": pd.Index(
                        [emission_type + " Power Cap" for emission_type in get_emission_types(
                            settings.global_settings
                        )]
                    ),
                },
            }

        return required_parameters
    
