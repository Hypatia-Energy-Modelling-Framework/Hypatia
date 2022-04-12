from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
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
