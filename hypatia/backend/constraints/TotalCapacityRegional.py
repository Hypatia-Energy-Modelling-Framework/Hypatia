from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import create_technology_columns
import pandas as pd

"""
Defines the annual upper and lower limit on the total capacity
of each technology within each region
"""
class TotalCapacityRegional(Constraint):
    MODES = [ModelMode.Planning]

    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalprodbycarrier must be defined"

    def rules(self):
        rules = []

        for reg in self.model_data.settings.regions:
            for key, value in self.variables.totalcapacity[reg].items():
                rules.append(
                    value - self.model_data.regional_parameters[reg]["tech_mintotcap"].loc[:, key].values
                    >= 0
                )
                rules.append(
                    value - self.model_data.regional_parameters[reg]["tech_maxtotcap"].loc[:, key] <= 0
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
                "tech_mintotcap": {
                    "sheet_name": "Min_totalcap",
                    "value": 0,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
                "tech_maxtotcap": {
                    "sheet_name": "Max_totalcap",
                    "value": 1e10,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
            }

        return required_parameters
