from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import available_resource_prod
import cvxpy as cp
import numpy as np

"""
Guarantees the adequecy of total capacity of each technology based on
the technology capacity factor and resource availability
"""
class ResourceTechAvailability(Constraint):
    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalcapacity must be defined"
        assert hasattr(self.variables, 'technology_prod'), "technology_prod must be defined"


    def rules(self):
        # reshape timeslice fraction
        timeslice_fraction = self.model_data.settings.timeslice_fraction
        if not isinstance(timeslice_fraction, int):
            timeslice_fraction.shape = (len(self.model_data.settings.time_steps), 1)

        rules = []
        for reg in self.model_data.settings.regions:
            for key in self.variables.technology_prod[reg].keys():
                if key != "Storage":
                    for indx, year in enumerate(self.model_data.settings.years):
                        available_prod = available_resource_prod(
                            self.variables.totalcapacity[reg][key][indx : indx + 1, :],
                            self.model_data.regional_parameters[reg]["res_capacity_factor"]
                            .loc[(year, slice(None)), (key, slice(None))]
                            .values,
                            timeslice_fraction,
                            self.model_data.regional_parameters[reg]["annualprod_per_unitcapacity"]
                            .loc[:, (key, slice(None))]
                            .values,
                        )
                        rules.append(
                            available_prod
                            - self.variables.technology_prod[reg][key][
                                indx
                                * len(self.model_data.settings.time_steps) : (indx + 1)
                                * len(self.model_data.settings.time_steps),
                                :,
                            ]
                            >= 0
                        )
                        rules.append(
                            cp.multiply(
                                cp.sum(available_prod, axis=0),
                                self.model_data.regional_parameters[reg]["tech_capacity_factor"].loc[
                                    year, (key, slice(None))
                                ],
                            )
                            - cp.sum(
                                self.variables.technology_prod[reg][key][
                                    indx
                                    * len(self.model_data.settings.time_steps) : (indx + 1)
                                    * len(self.model_data.settings.time_steps),
                                    :,
                                ],
                                axis=0,
                            )
                            >= 0
                        )
        return rules
