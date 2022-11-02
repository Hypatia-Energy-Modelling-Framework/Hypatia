# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 16:40:44 2022

@author: Gianluca Pellecchia
"""
import pandas as pd
import numpy as np
import unittest
import copy
from hypatia.backend.ModelSettings import ModelSettings
from hypatia.backend.ModelData import ModelData
from hypatia.utility.constants import ModelMode
from hypatia.backend.Build import BuildModel
from hypatia.backend.tests.TestSettings import (
    SingleNodeOperationResPenetrationTestSettings, SingleNodePlanningProductionTestSettings )#, SingleNodeOperationEmissionTestSettings,SingleNodePlanningEmissionTestSettings, SingleNodePlanningRampingTestSettings,MultiNodeOperationRampingTestSettings)
import hypatia.error_log.Exceptions as hypatiaException
from hypatia.core.main import Model
import cvxpy as cp


example_settings = SingleNodeOperationResPenetrationTestSettings()
settings = ModelSettings(
    ModelMode.Operation,
    example_settings.global_settings,
    example_settings.regional_settings,
)


# define the numerical parameters
regional_parameters = settings.default_regional_parameters

# Increment demand for elec to 1 for each timestamp
regional_parameters["reg1"]["demand"] += 1

# Increment the residual capacity for all techs
regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Elec_import"])] += 8760
regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["PV_park"])] += 8760
regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Heat_import"])] += 8760
regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["CHP"])] += 8760

regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

# Increment the cost for Elec_import so it is better to fulfil the demand using PV park
regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["PV_park"])] += 10000
regional_parameters["reg1"]["renewable_tech"].loc[:, (slice(None), ["PV_park"])] += 1
# regional_parameters["reg1"]["tech_min_production_share"].loc[:, (slice(None), ["PV_park"])] += 1
regional_parameters["reg1"]["renewable_electric_penetration"] += 1

model_data = ModelData(
    settings,
    settings.default_global_parameters,
    settings.default_trade_parameters,
    regional_parameters
)

model = BuildModel(model_data=model_data)
results = model._solve(verbosity=True, solver="GUROBI")

# Check that we used PV_park to produced elec 
supply_technology_use = pd.DataFrame(
    data=results.technology_prod["reg1"]["Supply"].value,
    index=pd.MultiIndex.from_product(
        [settings.years, settings.time_steps],
        names=["Years", "Timesteps"],
    ),
    columns=settings.technologies["reg1"]["Supply"],
)

CHP_technology_use = pd.DataFrame(
    data=results.technology_prod["reg1"]["Conversion_plus"].value,
    index=pd.MultiIndex.from_product(
        [settings.years, settings.time_steps],
        names=["Years", "Timesteps"],
    ),
    columns=settings.technologies["reg1"]["Conversion_plus"],
)