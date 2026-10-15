from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import get_emission_types
import pandas as pd
import cvxpy as cp
from hypatia.backend.constraints._terms import sum_terms

"""
Defines the CO2 emission cap across all regions
"""
class EmissionCapGlobal(Constraint):
    TOPOLOGY_TYPES = [TopologyType.MultiNode]
    _sum_terms = staticmethod(sum_terms)

    def _check(self):
        assert hasattr(self.variables, "emission_by_region"), "emission_by_region must be defined"

    def rules(self):
        rules = []
        n_years = len(self.model_data.settings.years)
        for emission_type in get_emission_types(self.model_data.settings.global_settings):
            global_emission_terms = []
            for reg in self.model_data.settings.regions:
                for key, value in self.variables.emission_by_region[reg][emission_type].items():
                    global_emission_terms.append(
                        cp.reshape(cp.sum(value, axis=1), (n_years, 1))
                    )
            global_emission = self._sum_terms(global_emission_terms)
            if global_emission is not None:
                global_emission_cap = self.model_data.global_parameters[
                        "global_emission_cap_annual"
                    ]["{} Global Emission Cap".format(emission_type)].values
                global_emission_cap.shape = global_emission.shape
                rules.append(global_emission_cap - global_emission >= 0)
        return rules

    def _required_global_parameters(settings):
        return {
            "global_emission_cap_annual": {
                "sheet_name": "Glob_emission_cap_annual",
                "value": 1e30,
                "index": pd.Index(settings.years, name="Years"),
                "columns": pd.Index(
                    [emission_type + " Global Emission Cap" for emission_type in get_emission_types(
                        settings.global_settings
                    )]
                ),
            },
        }
