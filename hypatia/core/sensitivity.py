# -*- coding: utf-8 -*-

from SALib.sample import saltelli,morris
import copy
from typing import Tuple,List,Optional
from hypatia.utility.constants import take_regional_sheets, take_ids, sheets_to_ids
from hypatia.analysis.postprocessing import dict_to_csv
import pandas as pd

SENS_METHODS = {
    "morris":morris,
    "saltelli": saltelli,
    }

import logging


logger = logging.getLogger(__name__)


def create_tuples(par_col:str):
    
    parts = par_col.split("(")[-1].split(")")[0].split(",")
    return tuple(parts)

def create_list(regions:str):
    
    parts = regions.split("[")[-1].split("]")[0].split(",")
    return list(parts)

class Parameter:

    def __init__(self,model,name:str,parameter:str,regions:List[str],parameter_col:Tuple[str],bound:List[float]):
        
        self._sets = model._StrData
        self.regions = regions
        self.parameter = parameter
        self.parameter_col = parameter_col
        self.bound = bound
        self.name = name


    @property
    def regions(self):
        return self._regions


    @regions.setter
    def regions(self,var):
        for reg in var:
            if reg not in self._sets.regions:
                raise ValueError()

        self._regions = var


    @property 
    def parameter(self):
        return self._parameter

    @parameter.setter
    def parameter(self,par):
        parameter_dict = take_regional_sheets(
            mode = self._sets.mode,
            technologies= self._sets.Technologies,
            regions = self.regions
            )

        for reg in self.regions:
            if par not in parameter_dict[reg]:
                raise ValueError()

        self._parameter = par

    @property
    def bound(self):
        return self._bound

    @bound.setter
    def bound(self,bound):

        if len(bound) != 2:
            print(bound)
            raise ValueError()

        if any([i<= -1 for i in bound]):
            raise ValueError()

        self._bound = bound

class Sensitivity:
    
    def __init__(self,model,method,path,results_path):
        self._model = model
        self._path = results_path
        self._parameters = []
        if method not in [*SENS_METHODS]:
            raise ValueError()
        self.method = method
        self._read_uncertain_parameters(path)
        
        
    def _read_uncertain_parameters(self,path):
        
        input_bounds =  pd.read_excel(path, index_col = [0], header =[0])
        
        for parameter,info in input_bounds.iterrows():
            
            self._parameters.append(
                Parameter(
                    model = self._model,
                    parameter = info.loc["parameter"],
                    regions = create_list(info.loc["regions"]),
                    parameter_col = create_tuples(info.loc["parameter_col"]),
                    bound = eval(info.loc["bound"]),
                    name = self._get_parameter_name()
                    )
            ) 
        
    

    def _get_parameter_name(self):

        _len = len(self._parameters)

        return f"Par{_len+1}"


    def generate_sample(self,**kwargs):
        
        num_vars = len(self._parameters)
        names = [par.name for par in self._parameters]
        bounds = [par.bound for par in self._parameters]

        problem = dict(
            num_vars = num_vars,
            names = names,
            bounds = bounds
            )

        function = SENS_METHODS[self.method]
        
        smp = pd.DataFrame(function.sample(problem=problem,**kwargs), columns=names)
        self._sample = smp
        
        return smp
    
    def run_sensitivity(self,solver,force_rewrite,path):
        
        new_model = copy.deepcopy(self._model)
        
        for row_num, row in self._sample.iterrows():
            for col,parameter in enumerate(self._parameters):
                
                db_parameter = sheets_to_ids[parameter.parameter]
                
                for reg in parameter.regions:
                    new_model._StrData.data[reg][db_parameter].loc[:,parameter.parameter_col] =\
                        self._model._StrData.data[reg][db_parameter].loc[:,parameter.parameter_col] * (1 + row.loc[parameter.name])
        
            dict_to_csv(new_model._StrData.data, '{}/samp_{}'.format(path, row_num))
                    
            
                
            new_model.run(solver=solver,force_rewrite=force_rewrite)
            new_model.to_csv(path='{}/results_{}'.format(path,row_num))
            

            
            


