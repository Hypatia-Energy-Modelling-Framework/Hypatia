from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import annual_activity
from hypatia.utility.utility import create_technology_columns
from hypatia.utility.utility import stack
import pandas as pd
import cvxpy as cp
import numpy as np

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
            
            for carr,value in self.variables.totalprodbycarrier[reg].items():
                
                prodbycarrier_annual = []

                for year in range(0, len(self.model_data.settings.years)):

                    totalprodbycarrier_annual_rest = cp.sum(
                        value[(year) * len(self.model_data.settings.time_steps) : (year+1) * len(self.model_data.settings.time_steps)],
                        axis=0,
                        keepdims=True
                    )

                    prodbycarrier_annual.append(totalprodbycarrier_annual_rest)


                totalprodbycarrier_annual = cp.vstack(prodbycarrier_annual)
                    
                for key in self.model_data.settings.technologies[reg].keys():

                    for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):
                        
                        if (
                            carr
                            in self.model_data.settings.regional_settings[reg]["Carrier_output"]
                            .loc[
                                self.model_data.settings.regional_settings[reg]["Carrier_output"]["Technology"]
                                == tech
                            ]["Carrier_out"]
                            .values
                        ):
                            if key == "Conversion_plus":
                                
                                techprodbycarrier_annual_conv = []
                                convprobycarr = cp.multiply(self.variables.technology_prod[reg][key][:, indx],self.model_data.regional_parameters[reg]["carrier_ratio_out"][(tech, carr)].values)
                                
                                for year in range(0, len(self.model_data.settings.years)):
                                    
                                    techprodbycarrier_annual_rest = cp.sum(
                                        convprobycarr[(year) * len(self.model_data.settings.time_steps) : (year+1) * len(self.model_data.settings.time_steps)],
                                        axis=0,
                                        keepdims=True,
                                    )
                                    techprodbycarrier_annual_conv.append(techprodbycarrier_annual_rest) 
                                    
                                techprodbycarrier_annual = cp.vstack(techprodbycarrier_annual_conv)
                                    
                                rules.append(
                                    techprodbycarrier_annual
                                    - self.model_data.regional_parameters[reg]["Conv_plus_max_production"].loc[:,(tech, carr, slice(None))]
                                    <= 0
                                )
                                rules.append(
                                    techprodbycarrier_annual
                                    - self.model_data.regional_parameters[reg]["Conv_plus_min_production"].loc[:,(tech, carr, slice(None))]
                                    >= 0
                                )
                                rules.append(
                                    techprodbycarrier_annual
                                    - cp.multiply(self.model_data.regional_parameters[reg]["Conv_plus_max_production_share"].loc[:,(tech, carr, slice(None))],totalprodbycarrier_annual)
                                    <= 0
                                )
                                rules.append(
                                    techprodbycarrier_annual
                                    - cp.multiply(self.model_data.regional_parameters[reg]["Conv_plus_min_production_share"].loc[:,(tech, carr, slice(None))],totalprodbycarrier_annual)
                                    >= 0
                                )

                            else:
                                
                                techprodbycarr_annual_other = []
                                
                                for year in range(0, len(self.model_data.settings.years)):

                                    techprodbycarrier_annual_rest_other = cp.sum(
                                        self.variables.technology_prod[reg][key][:, indx][(year) * len(self.model_data.settings.time_steps) : (year+1) * len(self.model_data.settings.time_steps)],
                                        axis=0,
                                        keepdims=True,
                                    )
                                    techprodbycarr_annual_other.append(techprodbycarrier_annual_rest_other) 
                                    
                                techprodbycarrier_annual_other = cp.vstack(techprodbycarr_annual_other)
                                
                                if key != "Transmission" and key != "Storage":
                                    
                                    rules.append(
                                        techprodbycarrier_annual_other
                                        - self.model_data.regional_parameters[reg]["tech_max_production"].loc[:, (key, tech, slice(None))]
                                        <= 0
                                    )
                                    rules.append(
                                        techprodbycarrier_annual_other
                                        - self.model_data.regional_parameters[reg]["tech_min_production"].loc[:, (key, tech, slice(None))]
                                        >= 0
                                    )
                                    rules.append(
                                        techprodbycarrier_annual_other
                                        - cp.multiply(self.model_data.regional_parameters[reg]["tech_max_production_share"].loc[:, (key, tech, slice(None))],totalprodbycarrier_annual)
                                        <= 0
                                    )
                                    rules.append(
                                        techprodbycarrier_annual_other
                                        - cp.multiply(self.model_data.regional_parameters[reg]["tech_min_production_share"].loc[:, (key, tech, slice(None))],totalprodbycarrier_annual)
                                        >= 0
                                    )                         
                            
        return rules

    def _required_regional_parameters(settings):
        required_parameters = {}
        for reg in settings.regions:
            indexer = create_technology_columns(
                settings.technologies[reg],
                ignored_tech_categories=["Demand", "Storage", "Transmission", "Conversion_plus"],
            )

            required_parameters[reg] = {
                "tech_max_production": {
                    "sheet_name": "Max_production",
                    "value": 1e20,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
                "tech_min_production": {
                    "sheet_name": "Min_production",
                    "value": 0,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
                "tech_max_production_share": {
                    "sheet_name": "Max_production_share",
                    "value": 1,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                },
                "tech_min_production_share": {
                    "sheet_name": "Min_production_share",
                    "value": 0,
                    "index": pd.Index(settings.years, name="Years"),
                    "columns": indexer,
                }
            }    
                
        return required_parameters
    
    
    
