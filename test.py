# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 11:37:41 2023

@author: NAMAZIFN
"""

from hypatia import Model,Plotter, Sensitivity
#%%
milp_test = Model(
    path = 'test/connection_MILP/sets', 
    mode = 'Planning', period_step = 15)
#%%
##milp_test.create_data_excels(path = 'test/connection_MILP/parameters')
#%%
milp_test.read_input_data(
    path = 'test/connection_MILP/parameters'
)
#%%
milp_test.run(solver = "gurobi", verbosity= True)
#%%
milp_test.to_csv(path="test/connection_MILP/results")
#%%
