from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import _calc_production_overall


"""
Defines the upper and lower limit for the aggregated annual production
of the technologies over all the regions
"""
class AnnualProductionGlobal(Constraint):
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert hasattr(self.variables, "production_annual"), "production_annual must be defined"

    def rules(self):
        production_overall = _calc_production_overall(
            self.model_data.settings.global_settings["Technologies_glob"],
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.technologies,
            self.variables.production_annual,
        )

        rules = []
        for tech, value in production_overall.items():
            rules.append(
                value - self.model_data.global_parameters["global_min_production"].loc[:, tech] >= 0
            )
            rules.append(
                value - self.model_data.global_parameters["global_max_production"].loc[:, tech] <= 0
            )
        return rules
