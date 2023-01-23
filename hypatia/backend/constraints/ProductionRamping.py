from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import create_technology_columns
import pandas as pd
import cvxpy as cp
import numpy as np

"""
Defines the annual upper and lower limit on the total capacity
of each technology within each region
"""
class ProductionRamping(Constraint):
    # it runs on both operation and planning, single- and multi-region

    def __get_energy_prod_differences(self):
        """Creates variables to constrain the increase and decrease 
        in energy production when passing from one timestep to the next"""
        
        # Create a dataframe containing the differences between the energy production of each tech 
        # in each timestep and the production in the previous timestep
        energy_prod_differences = {}
        
        # for each region
        for reg in self.model_data.settings.regions:
            energy_prod_differences_regional = {}
            
            #for each tech, except demand, transmission, and storage
            for tech_type in self.model_data.settings.technologies[reg].keys():
                if tech_type == "Demand" or tech_type == "Transmission" or tech_type == "Storage":
                    continue
                # select the first row
                first_row = cp.reshape(
                    self.variables.technology_prod[reg][tech_type][0,:], 
                    (1, self.variables.technology_prod[reg][tech_type][0,:].shape[0])
                )
                
                # in the case the timesteps are just one, the shifted dataframe containing the energy production
                # will only be the first row; if timesteps are > 1 instead we have a shifted dataframe
                if self.variables.technology_prod[reg][tech_type].shape[0] > 1:
                    shifted_prod = cp.vstack([first_row, (self.variables.technology_prod[reg][tech_type][:-1,:])])
                else:
                    shifted_prod = first_row

                # compute the difference between the energy production in each timestep and the the production in the previouos timestep
                energy_prod_differences_regional[tech_type] = self.variables.technology_prod[reg][tech_type] - shifted_prod
            energy_prod_differences[reg] = energy_prod_differences_regional
        return energy_prod_differences ## 8760*nyears x ntechs     
        
        
    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalcapacity must be defined"
    
    def rules(self):
        rules = []

        for reg in self.model_data.settings.regions:
            for tech_type in self.model_data.settings.technologies[reg].keys():
                if tech_type == "Demand" or tech_type == "Transmission" or tech_type == "Storage":
                    continue
                max_percentage_ramps = self.model_data.regional_parameters[reg]["prod_max_ramp"].loc[:, tech_type]
                max_percentage_ramps = max_percentage_ramps.reindex(max_percentage_ramps.index.repeat(
                    len(self.model_data.settings.years))
                ).values
                min_percentage_ramps = self.model_data.regional_parameters[reg]["prod_min_ramp"].loc[:, tech_type]
                min_percentage_ramps = min_percentage_ramps.reindex(min_percentage_ramps.index.repeat(
                    len(self.model_data.settings.years))
                ).values

                max_ramp_in_timestep = cp.multiply(self.variables.totalcapacity[reg][tech_type], max_percentage_ramps)
                max_ramp_in_timestep_rows = []
                for years_index in range(0, max_ramp_in_timestep.shape[0]):
                    for _ in range(0, len(self.model_data.settings.time_steps)):
                        max_ramp_in_timestep_rows.append(max_ramp_in_timestep[years_index])
                max_ramp_in_timestep = cp.vstack(max_ramp_in_timestep_rows)

                min_ramp_in_timestep = cp.multiply(self.variables.totalcapacity[reg][tech_type], min_percentage_ramps)
                min_ramp_in_timestep_rows = []
                for years_index in range(0, min_ramp_in_timestep.shape[0]):
                    for _ in range(0, len(self.model_data.settings.time_steps)):
                        min_ramp_in_timestep_rows.append(min_ramp_in_timestep[years_index])
                min_ramp_in_timestep = cp.vstack(min_ramp_in_timestep_rows)

                energy_prod_differences = self.__get_energy_prod_differences()

                # rules.append(
                #     energy_prod_differences[reg][tech_type] <= max_ramp_in_timestep
                # )
                # rules.append(
                #     energy_prod_differences[reg][tech_type] * -1 <= min_ramp_in_timestep
                # )
        return rules

    def _required_regional_parameters(settings):
        required_parameters = {}
        for reg in settings.regions:
            indexer = create_technology_columns(
                settings.technologies[reg],
                ignored_tech_categories=["Demand", "Transmission", "Storage"],
            )
            required_parameters[reg] = {
                "prod_max_ramp": {
                    "sheet_name": "Max_prod_ramps",
                    "value": 1,
                    "index": pd.Index(
                        ["Max_production_ramp_in_a_timestep"], name="Performance Parameter"
                    ),
                    "columns": indexer,
                },
                "prod_min_ramp": {
                    "sheet_name": "Min_prod_ramps",
                    "value": 1,
                    "index": pd.Index(
                        ["Min_production_ramp_in_a_timestep"], name="Performance Parameter"
                    ),
                    "columns": indexer,
                },
            }

        return required_parameters
