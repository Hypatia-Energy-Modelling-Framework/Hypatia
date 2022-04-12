from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import _calc_variable_overall

"""
Defines the annual upper and lower limit on the aggregated total capacity
of each technology over all the regions
"""
class TotalCapacityGlobal(Constraint):
    MODES = [ModelMode.Planning]
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalprodbycarrier must be defined"

    def rules(self):
        totalcapacity_overall = _calc_variable_overall(
            self.model_data.settings.global_settings["Technologies_glob"],
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.technologies,
            self.variables.totalcapacity,
        )

        rules = []
        for tech, value in totalcapacity_overall.items():
            rules.append(
                value - self.model_data.global_parameters["global_mintotcap"].loc[:, tech].values
                >= 0
            )
            rules.append(
                value - self.model_data.global_parameters["global_maxtotcap"].loc[:, tech].values
                <= 0
            )

        return rules
