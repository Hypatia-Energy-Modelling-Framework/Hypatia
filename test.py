# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 11:37:41 2023

@author: NAMAZIFN
"""

from hypatia import Model,Plotter, Sensitivity
#%%
offshore_test = Model(
    path = 'test/yeees/central_offshore/sets', 
    mode = 'Planning', period_step = 15)
#%%
#offshore_test.create_data_excels(path = 'test/yeees/central_offshore/parameters_update')
#%%
offshore_test.read_input_data(
    path = 'test/yeees/central_offshore/parameters'
)
#%%
offshore_test.run(solver = "gurobi", verbosity= True, force_rewrite=True, Method=3)
#%%
offshore_test.to_csv(path="test/yeees/central_offshore/results")
#%%
