
from SALib.sample import satelli,morris

from typing import Tuple,List,Optional
from hypatia.utility.constants import take_regional_sheets

SENS_METHODS = {
    "morris":morris,
    "satelli": satelli,
    }

class Parameter:

    def __init__(self,model,name:str,parameter:str,region:str,parameter_col:Tuple[str],bound:List[float]):
        
        self._sets = model._StrData
        self.region = region
        self.parameter = parameter
        self.parameter_col = parameter_col
        self.bound = bound
        self.name = name


    @property
    def region(self):
        return self._region


    @region.setter
    def region(self,var):
        if var not in self._sets.regions:
            raise ValueError()

        self._region = var


    @property 
    def parameter(self):
        pass

    @parameter.setter
    def parameter(self,par):
        parameter_list = take_regional_sheets(
            mode = self._sets.mode,
            technologies= self._sets.Technologies,
            regions = [self.region]
            )[self.region]


        if par not in parameter_list:
            raise ValueError()

        self._parameter = par

    @property
    def bound(self):
        return self._bound

    @bound.setter
    def bound(self,bound):

        if len(bound) != 2:
            raise ValueError()

        if any([-1 <= i for i in bound]):
            raise ValueError()

        self._bound = bound
        

class Sensitivity:
    
    def __init__(self,model,method,results_path):
        self._model = model
        self._path = results_path
        self._parameters = []
        if method not in [*SENS_METHODS]:
            raise ValueError()
        self.method = method

    def _get_parameter_name(self):

        _len = len(self._parameters)

        return f"Par{_len+1}"

    def add_parameter(self,parameter:str,region:str,parameter_col:Tuple[str],bound:List[float]):
        self._parameters.append(
            Parameter(
                model=self._model,
                parameter=parameter,
                region=region,
                parameter_col=parameter_col,
                bound=bound,
                name = self._get_parameter_name()
                )
        ) 


    def sample(self,**kwargs):
        
        num_vars = len(self._parameters)
        names = [par.name for par in self._parameters]
        bounds = [par.bound for par in self._parameters]

        problem = dict(
            num_vars = num_vars,
            names = names,
            bounds = bounds
            )

        function = SENS_METHODS[self.method]

        return function.sample(**kwargs)

