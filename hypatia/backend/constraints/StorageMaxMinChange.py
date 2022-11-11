from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import get_regions_with_storage
import cvxpy as cp
import numpy as np

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
                
                BESS_capacity = []
                for _ in enumerate(self.model_data.settings.time_steps):
                    BESS_capacity.append(self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :])
                Battery_capacity = cp.vstack(BESS_capacity)
                    
                min_BESS_cap = []
                for _ in enumerate(self.model_data.settings.time_steps):
                    min_BESS_cap.append(cp.multiply(
                        self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                        self.model_data.regional_parameters[reg]["storage_min_SOC"].values[
                            indx : indx + 1, :
                        ]))       
                min_BESS_SOC = cp.vstack(min_BESS_cap)                       
                                                        
                rules.append(
                    Battery_capacity
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
                    - min_BESS_SOC
                    >= 0
                )
                
            # # print(self.variables.storage_SOC[reg])
            
            # SOC_storage_init = []
            # for idx in range(0,len(self.variables.storage_SOC),len(self.model_data.settings.time_steps)):
            #     SOC_storage_init.append(self.variables.storage_SOC[reg][idx:idx+1,:])
                
            # print(np.shape(SOC_storage_init))
            # BESS_SOC_init = cp.vstack(SOC_storage_init)
            
            # SOC_storage_end = []
            # for idxx in range(len(self.model_data.settings.time_steps)-1,len(self.variables.storage_SOC),len(self.model_data.settings.time_steps)):
            #     SOC_storage_end.append(self.variables.storage_SOC[reg][idxx,:])
                
            # print(np.shape(SOC_storage_end))
            # BESS_SOC_end = cp.vstack(SOC_storage_end)
                Storage_SOC = self.variables.storage_SOC[reg][
                    indx
                    * len(self.model_data.settings.time_steps) : (indx + 1)
                    * len(self.model_data.settings.time_steps),
                    :,
                ]
                
                rules.append(
                    Storage_SOC[0:1,:]
                    - cp.multiply(
                        self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                        self.model_data.regional_parameters[reg]["storage_min_SOC"].values[indx : indx + 1, :]
                    )
                    == 0
                )
                
                rules.append(
                    Storage_SOC[len(self.model_data.settings.time_steps)-1:len(self.model_data.settings.time_steps),:]
                    - cp.multiply(
                        self.variables.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                        self.model_data.regional_parameters[reg]["storage_min_SOC"].values[indx : indx + 1, :]
                    )
                    == 0
                )
        return rules
