from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import create_technology_columns
import pandas as pd

"""
Defines the upper and lower limit on the annual new installed capacity
of each technology within each region
"""
class NewCapacityRegional(Constraint):
    MODES = [ModelMode.Planning]

    def _check(self):
        assert self.variables.real_new_capacity != None

    def rules(self):
        rules = []
        for reg in self.model_data.settings.regions:
            for key, value in self.variables.real_new_capacity[reg].items():
                rules.append(
                    value >= self.model_data.regional_parameters[reg]["tech_min_newcap"].loc[:, key]
                )
                rules.append(
                    value <= self.model_data.regional_parameters[reg]["tech_max_newcap"].loc[:, key]
                )
        return rules

    def _required_regional_parameters(settings):
        required_parameters = {}
        for reg in settings.regions:
            indexer = create_technology_columns(
                settings.technologies[reg],
                ignored_tech_categories=["Demand"],
            )

            required_parameters[reg] = {
                "tech_min_newcap": {
                    "sheet_name": "Min_newcap",
                    "value": 0,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
                "tech_max_newcap": {
                    "sheet_name": "Max_newcap",
                    "value": 1e10,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                }
            }
        return required_parameters
