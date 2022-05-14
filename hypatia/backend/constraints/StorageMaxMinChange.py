from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import get_regions_with_storage


"""
Defines the maximum and minumum alllowed storage state of charge in each
timestep of the year based on the total nominal capacity and the minimum
state of charge factor
"""
class StorageMaxMinChange(Constraint):
    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalcapacity must be defined"

    def rules(self):
        rules = []
        for reg in get_regions_with_storage(self.model_data.settings):
            for indx, year in enumerate(self.model_data.settings.years):
                rules.append(
                    self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :]
                    - self.variables.storage_SOC[reg][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    >= 0
                )
                rules.append(
                    self.variables.storage_SOC[reg][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    - cp.multiply(
                        self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                        self.model_data.regional_parameters[reg]["storage_min_SOC"].values[
                            indx : indx + 1, :
                        ],
                    )
                    >= 0
                )
        return rules
