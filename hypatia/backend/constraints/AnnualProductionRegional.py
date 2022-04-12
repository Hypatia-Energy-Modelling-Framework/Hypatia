from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import annual_activity

"""
Defines the upper and lower limit for the annual production of the technologies
within each region
"""
class AnnualProductionRegional(Constraint):
    def _check(self):
        assert self.variables.technology_prod != None, "technology_prod cannot be None"

    def rules(self):
        rules = []
        for reg in self.model_data.settings.regions:
            for key, value in self.variables.technology_prod[reg].items():
                production_annual = annual_activity(
                    value, self.model_data.settings.years, self.model_data.settings.time_steps,
                )
                if key != "Transmission" and key != "Storage":
                    rules.append(
                        production_annual
                        - self.model_data.regional_parameters[reg]["tech_max_production"].loc[
                            :, (key, slice(None))
                        ]
                        <= 0
                    )
                    rules.append(
                        production_annual
                        - self.model_data.regional_parameters[reg]["tech_min_production"].loc[
                            :, (key, slice(None))
                        ]
                        >= 0
                    )
        return rules
