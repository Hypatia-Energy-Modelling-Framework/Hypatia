from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import get_emission_types
import pandas as pd
import cvxpy as cp
from hypatia.backend.constraints._terms import sum_terms, normalize_carrier, is_power_carrier

"""
Defines the CO2 emission cap within each region for all the sectors
Defines the CO2 emission cap within each region for power sector only (electricity production) 
"""
class EmissionCapRegional(Constraint):
    _normalize_carrier = staticmethod(normalize_carrier)
    _is_power_carrier = staticmethod(is_power_carrier)
    _sum_terms = staticmethod(sum_terms)

    def _check(self):
        assert hasattr(self.variables, "emission_by_region"), "emission_by_region must be defined"

    def rules(self):
        rules = []
        n_years = len(self.model_data.settings.years)
        
        for emission_type in get_emission_types(self.model_data.settings.global_settings):

            for reg in self.model_data.settings.regions:
                regional_emission_terms = []
                for key, value in self.variables.emission_by_region[reg][emission_type].items():
                    regional_emission_terms.append(
                        cp.reshape(cp.sum(value, axis=1), (n_years, 1))
                    )
                regional_emission = self._sum_terms(regional_emission_terms)
                if regional_emission is not None:
                    emission_cap = self.model_data.regional_parameters[reg]["emission_cap_annual"][
                        "{} Global Cap".format(emission_type)
                    ].values
                    emission_cap.shape = regional_emission.shape
                    rules.append(emission_cap - regional_emission >= 0)

                emission_power_terms = []
                for key in self.variables.emission_by_region[reg][emission_type].keys():
                    
                    for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):
                        carrier_outputs = (
                            self.model_data.settings.regional_settings[reg]["Carrier_output"]
                            .loc[
                                self.model_data.settings.regional_settings[reg]["Carrier_output"]["Technology"]
                                == tech
                            ]["Carrier_out"]
                            .values
                        )
                        if any(self._is_power_carrier(carr) for carr in carrier_outputs):
                            emission_power_terms.append(
                                cp.reshape(
                                    self.variables.emission_by_region[reg][emission_type][key][:,indx],
                                    (n_years, 1)
                                )
                            )
                emission_power = self._sum_terms(emission_power_terms)
                if emission_power is not None:
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
                    "value": 1e30,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": pd.Index(
                        [emission_type + " Global Cap" for emission_type in get_emission_types(
                            settings.global_settings
                        )]
                    ),
                },
                "emission_cap_annual_power": {
                    "sheet_name": "Emission_cap_annual_power",
                    "value": 1e30,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": pd.Index(
                        [emission_type + " Power Cap" for emission_type in get_emission_types(
                            settings.global_settings
                        )]
                    ),
                },
            }

        return required_parameters
    
