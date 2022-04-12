from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)


"""
Ensure sthe trade balance among any pairs of regions before the transmission
loss
"""
class TradeBalance(Constraint):
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert self.variables.line_import != None, "line_import cannot be None"
        assert self.variables.line_export!= None, "line_export cannot be None"

    def rules(self):
        rules = []
        for reg in self.model_data.settings.regions:
            for key in self.variables.line_import[reg].keys():
                rules.append(
                    self.variables.line_import[reg][key]
                    - self.variables.line_export[key][reg]
                    == 0
                )
        return rules
