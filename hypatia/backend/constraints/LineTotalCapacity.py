from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)

"""
Defines the upper and lower limit on the annual total capacity of the
inter-regional links
"""
class LineTotalCapacity(Constraint):
    MODES = [ModelMode.Planning]
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert hasattr(self.variables, 'line_totalcapacity'), "line_totalcapacity must be defined"

    def rules(self):
        rules = []
        for key, value in self.variables.line_totalcapacity.items():
            rules.append(
                value <= self.model_data.trade_parameters["line_maxtotcap"][key].values
            )
            rules.append(
                value >= self.model_data.trade_parameters["line_mintotcap"][key].values
            )
        return rules
