# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 11:37:41 2023

@author: NAMAZIFN
"""

from hypatia import Model,Plotter, Sensitivity
#%%
test = Model(
    path = 'test/yeees_modified/blue_hydrogen/sets', 
    mode = 'Planning', period_step = 5)
#%%
test.create_data_excels(path = 'test/yeees_modified/blue_hydrogen/parameters')
#%%
test.read_input_data(
    path = 'test/test_storage/parameters'
)
#%%
test.run(solver = "gurobi", verbosity= True)
#%%
test.to_csv(path="test/yeees_modified/central_offshore_H2/results")
#%%
import pandas as pd
#%%
#salvage_line_new = offshore_test.model.salvage_inv_line
#%%
#salvage_new = offshore_test.model.salvage_inv
#%%
#SOC = offshore_test.model.storage_SOC["reg4"].value
#SOC_output = pd.DataFrame(SOC)
#%%
#charge = offshore_test.results["use_by_tech"]["reg4"]["Storage"]
#with pd.ExcelWriter(
    #r"test/test_storage/charge.xlsx") as writer:
    #charge.to_excel(writer)
#%%
#discharge = offshore_test.results["production_by_tech"]["reg4"]["Storage"]
#with pd.ExcelWriter(
    #r"test/test_storage/discharge.xlsx") as writer:
    #discharge.to_excel(writer)
