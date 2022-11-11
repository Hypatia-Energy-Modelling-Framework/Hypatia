from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import (
    get_regions_with_storage,
    storage_max_flow
)


"""
Defines the maximum and minimum allowed storage inflow and outflow in each
hour of the year based on the total capacity, the capacity factor and
the storage charge and discharge time
"""
class StorageMaxFlowInOut(Constraint):
    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalcapacity must be defined"
        assert self.variables.technology_use != None, "technology_use must not be None"
        assert self.variables.technology_prod != None, "technology_prod must not be None"

    def rules(self):
        timeslice_fraction = self.model_data.settings.timeslice_fraction
        if not isinstance(timeslice_fraction, int):
            timeslice_fraction.shape = (len(self.model_data.settings.time_steps), 1)

        rules = []
        for reg in get_regions_with_storage(self.model_data.settings):
            for indx, year in enumerate(self.model_data.settings.years):
                max_storage_flow_in = storage_max_flow(
                    self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                    self.model_data.regional_parameters[reg]["storage_charge_time"].values,
                    self.model_data.regional_parameters[reg]["tech_availability"]["Storage"].values[
                        indx : indx + 1, :
                    ],
                    timeslice_fraction,
                )

                max_storage_flow_out = storage_max_flow(
                    self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                    self.model_data.regional_parameters[reg]["storage_discharge_time"].values,
                    self.model_data.regional_parameters[reg]["tech_availability"]["Storage"].values[
                        indx : indx + 1, :
                    ],
                    timeslice_fraction,
                )

                rules.append(
                    max_storage_flow_in
                    - self.variables.technology_use[reg]["Storage"][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    >= 0
                )

                rules.append(
                    max_storage_flow_out
                    - self.variables.technology_prod[reg]["Storage"][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    >= 0
                )
        return rules 
