from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
import numpy as np
import pandas as pd


"""
Defines the CO2 emission cap across all regions
"""
class EmissionCapGlobal(Constraint):
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert hasattr(self.variables, "regional_emission"), "regional_emission must be defined"

    def rules(self):
        global_emission = np.zeros(
            (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps), 1)
        )
        for reg in self.model_data.settings.regions:
            global_emission += self.variables.regional_emission[reg]

        global_emission_cap = self.model_data.global_parameters[
            "global_emission_cap_annual"
        ].values
        global_emission_cap.shape = global_emission.shape
        return [global_emission_cap - global_emission >= 0]

    def _required_global_parameters(settings):
        return {
            "global_emission_cap_annual": {
                "sheet_name": "Glob_emission_cap_annual",
                "value": 1e30,
                "index": pd.Index(settings.years, name="Years"),
                "columns": pd.Index(["Global Emission Cap"]),
            },
        }
