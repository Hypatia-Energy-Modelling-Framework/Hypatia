from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import create_technology_columns
import pandas as pd
import cvxpy as cp
import numpy as np


"""
Defines the relationship between the input and output activity of
conversion, transmission and conversion-plus technologies
"""
class TechEfficency(Constraint):
    def _check(self):
        assert self.variables.technology_prod != None, "technology_prod cannot be None"
        assert self.variables.technology_use != None, "technology_use cannot be None"

    def rules(self):
        rules = []
        for reg in self.model_data.settings.regions:
            for key, value in self.variables.technology_prod[reg].items():
                if key != "Supply" and key != "Storage":
                    tech_efficiency_reshape = pd.concat(
                        [self.model_data.regional_parameters[reg]["tech_efficiency"][key]]
                        * len(self.model_data.settings.time_steps)
                    ).sort_index()

                    rules.append(
                        value
                        - cp.multiply(
                            self.variables.technology_use[reg][key],
                            tech_efficiency_reshape.values,
                        )
                        == 0
                    )
        return rules

    def _required_regional_parameters(settings):
        required_parameters = {}
        for reg in settings.regions:
            indexer = create_technology_columns(
                settings.technologies[reg],
                ignored_tech_categories=["Demand", "Storage"],
            )

            required_parameters[reg] = {
                "tech_efficiency": {
                    "sheet_name": "Tech_efficiency",
                    "value": 1,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
            }

        return required_parameters
