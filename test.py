# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 11:37:41 2023

@author: NAMAZIFN
"""

from hypatia import Model,Plotter, Sensitivity
#%%
offshore_test = Model(
    path = 'test/test_storage/sets', 
    mode = 'Planning', period_step = 15)
#%%
#offshore_test.create_data_excels(path = 'test/yeees_modified/central_offshore_H2/parameters')
#%%
offshore_test.read_input_data(
    path = 'test/test_storage/parameters'
)
#%%
offshore_test.run(solver = "gurobi", verbosity= True)
#%%
offshore_test.to_csv(path="test/yeees_modified/central_offshore_H2/results")
#%%
import pandas as pd
#%%
SOC = offshore_test.model.storage_SOC["reg4"].value
SOC_output = pd.DataFrame(SOC)
with pd.ExcelWriter(
    r"test/test_storage/SOC.xlsx") as writer:
    SOC_output.to_excel(writer)

#%%
charge = offshore_test.results["use_by_tech"]["reg4"]["Storage"]
with pd.ExcelWriter(
    r"test/test_storage/charge.xlsx") as writer:
    charge.to_excel(writer)
