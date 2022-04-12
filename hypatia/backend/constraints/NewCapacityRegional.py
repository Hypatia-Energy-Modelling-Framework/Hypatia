from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)

"""
Defines the upper and lower limit on the annual new installed capacity
of each technology within each region
"""
class NewCapacityRegional(Constraint):
    MODES = [ModelMode.Planning]

    def _check(self):
        assert self.variables.new_capacity != None

    def rules(self):
        rules = []
        for reg in self.model_data.settings.regions:
            for key, value in self.variables.new_capacity[reg].items():
                rules.append(
                    value >= self.model_data.regional_parameters[reg]["tech_min_newcap"].loc[:, key]
                )
                rules.append(
                    value <= self.model_data.regional_parameters[reg]["tech_max_newcap"].loc[:, key]
                )
        return rules
