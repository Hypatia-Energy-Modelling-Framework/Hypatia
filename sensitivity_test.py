# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 15:45:44 2022

@author: NAMAZIFN
"""

from hypatia import Model,Plotter,Sensitivity
#%%
Belgium = Model(
    path = 'test/final_case/sets', 
    mode = 'Planning' 
)
#%%
# Belgium.create_data_excels(
#     path = 'test/final_case/parameters_new'
#     )
#%%
Belgium.read_input_data(
    path = 'test/final_case/parameters'
)
#%%
Belgium.run(
    solver = 'scipy',
    verbosity = True,
)
#%%
Belgium.to_csv(path='test/final_case/results')
#%%
sensitivity_1 = Sensitivity(
    model = Belgium,
    method = "saltelli",
    path = 'test/final_case/sensitivity1.xlsx',
    results_path = 'test/sensitivity/results' 
    )
#%%
sensitivity_1.generate_sample(N=2)
#%%
sensitivity_1.run_sensitivity(solver='scipy',force_rewrite=True,path='test/final_case')
#%%
Belgium.create_config_file(path=r'test/final_case/config.xlsx')
#%%
from plotly import graph_objs as go
from plotly.subplots import make_subplots
import plotly.offline as pltly

