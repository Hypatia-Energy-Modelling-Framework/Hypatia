from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
import pandas as pd

"""
Defines the CO2 emission cap within each region
"""
class EmissionCapRegional(Constraint):
    def _check(self):
        assert hasattr(self.variables, "regional_emission"), "regional_emission must be defined"
        assert hasattr(self.variables, "CO2_equivalent"), "regional_emission must be defined"

    def rules(self):
        rules = []
        for reg in self.model_data.settings.regions:
            for key, value in self.variables.CO2_equivalent[reg].items():
                emission_cap = self.model_data.regional_parameters[reg]["emission_cap_annual"].values
                emission_cap.shape = self.variables.regional_emission[reg].shape

            rules.append(emission_cap - self.variables.regional_emission[reg] >= 0)

        return rules

    def _required_regional_parameters(settings):
        required_parameters = {}
        for reg in settings.regions:
            required_parameters[reg] = {
                "emission_cap_annual": {
                    "sheet_name": "Emission_cap_annual",
                    "value": 1e10,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": pd.Index(["Emission Cap"]),
                },
            }

        return required_parameters
