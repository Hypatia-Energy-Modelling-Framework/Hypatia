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
Defines lower limit for the annual electric production from renewable energy technologies
"""
class ElectrolysisConsumption(Constraint):
    
    def _check(self):
        assert self.variables.technology_prod != None, "technology_prod cannot be None"  
        assert self.variables.totalprodbycarrier != None, "totalprodbycarrier cannot be None"
        assert self.variables.technology_use != None, "technology_prod cannot be None"  
        assert self.variables.totalusebycarrier != None, "totalprodbycarrier cannot be None"

    def __renewable_electicity_production_calc(self):
        
        renewable_elec_prod = {}
        
        for reg in self.model_data.settings.regions:        
            
            techprodelec_annual_regional = {}
                    
            for key in self.model_data.settings.technologies[reg].keys():
                
                if key != "Storage" and key != "Demand" and key != "Transmission": 

                    for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):
                        
                        if self.model_data.regional_parameters[reg]["renewable_tech"][(key,tech)].values == 1:
                            
                            for carr,value in self.variables.totalprodbycarrier[reg].items():
                                
                                if carr != 'Electricity':
                                    continue
                        
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

                                        techprodelec_annual_conv = []
                                        convprodelec = cp.multiply(self.variables.technology_prod[reg][key][:, indx],self.model_data.regional_parameters[reg]["carrier_ratio_out"][(tech, carr)].values)
                                        
                                        
                                        for year in range(0, len(self.model_data.settings.years)):
                                            
                                            techprodelec_annual_rest = cp.sum(
                                                convprodelec[(year) * len(self.model_data.settings.time_steps) : (year+1) * len(self.model_data.settings.time_steps)],
                                                axis=0,
                                                keepdims=True,
                                            )
                                            techprodelec_annual_conv.append(techprodelec_annual_rest) 
                                            
                                        techprodelec_annual_regional[tech] = cp.vstack(techprodelec_annual_conv)

                                    else: 
                                        
                                        techprodelec_annual_other = []
                                                                        
                                        for year in range(0, len(self.model_data.settings.years)):
                                            
                                            othertechprodelec_annual_rest = cp.sum(
                                                self.variables.technology_prod[reg][key][:, indx][(year) * len(self.model_data.settings.time_steps) : (year+1) * len(self.model_data.settings.time_steps)],
                                                axis=0,
                                                keepdims=True,
                                            )
                                            techprodelec_annual_other.append(othertechprodelec_annual_rest) 
                                            
                                        techprodelec_annual_regional[tech] = cp.vstack(techprodelec_annual_other)

            renewable_elec_prod[reg] = techprodelec_annual_regional
        return renewable_elec_prod
    
    def rules(self):
        rules = [] 
        
        renewable_elec_prod = self.__renewable_electicity_production_calc()
        
        for reg in self.model_data.settings.regions: 

            renewable_elec_prod_annual = sum(renewable_elec_prod[reg].values())
            
            for key in self.model_data.settings.technologies[reg].keys():

                for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):
                    
                    if tech != "Electrolysis":
                        continue
                        
                    techuse_annual = []
                                                    
                    for year in range(0, len(self.model_data.settings.years)):
                                                            
                        usetech_annual = cp.sum(
                            self.variables.technology_use[reg][key][:,indx][(year) * len(self.model_data.settings.time_steps) : (year+1) * len(self.model_data.settings.time_steps)],
                            axis=0,
                            keepdims=True,
                        )
                        techuse_annual.append(usetech_annual)
                        
                    electrolysis_use_annual_regional = cp.vstack(techuse_annual)
            
            rules.append(
                electrolysis_use_annual_regional -
                renewable_elec_prod_annual                
                <= 0
            )                 
                    
        return rules

    
    
    
