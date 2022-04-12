from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)

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
