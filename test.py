# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 11:37:41 2023

@author: NAMAZIFN
"""


from hypatia import Model,Plotter, Sensitivity

#%%
test = Model(
    path = 'test/Belgian_case/tests/test_single_binary/central_offshore_offshore_final_v3/sets', 
    mode = 'Planning', period_step = 10)
#%%
test.create_data_excels(path = 'test/Belgian_case/tests/test_single_binary/central_offshore_offshore_final_v3/parameters_new')
#%%
test.read_input_data(
    path = 'test/yeees_final_v2/blue_hydrogen_final_mod/parameters'
)
#%%
#import gurobipy

#env = gurobipy.Env()
#env.setParam("LogFile","log.log")
test.run(solver = "gurobi", verbosity= True)
#%%
test.to_csv(path="test/yeees_final_v2/blue_hydrogen_final_mod/results",sep=";")
#%%
#import pandas as pd
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

#%%
import pandas as pd
import os
def dict_to_csv(Dict, path):
    """Writes nested dicts  to csv"""

    for key, value in Dict.items():
        if isinstance(value, pd.DataFrame):
            value.to_csv(f"{path}//{key}.csv",sep=",")
        else:
            new_path = f"{path}//{key}"
            os.makedirs(new_path, exist_ok=True)
            dict_to_csv(value, new_path)
            #%%
cost = test.results["variable_cost"]["reg1"]["Conversion"]
#%%
test.to_csv()
#%%
test._StrData.data["reg1"]["interest_rate"]

#%%
rate = 0.05
step = 5
import numpy as np
import pandas as pd



def var_cost(df,rate,step):
    df = df.groupby(level=0).sum()
    years = df.index.tolist()
    Y = -1 * np.arange(len(years))*step
    discount = np.power(1+rate, Y)
    
    
    
    res = pd.DataFrame(index=df.index,columns=df.columns)
    
    for idx,col in df.iteritems():
        res.loc[col.index,idx] = col.values * discount
    
    return res
#%%

a = var_cost(cost,0.05,5)


#%%

main_path = r"C:\Users\NAMAZIFN\OneDrive - VITO\Documents\GitHub\Hypatia\test\yeees_modified\blue_hydrogen\results_"

reg_var = [
    "variable_cost",
    "fix_cost",
    ]

line_var = [
    ""
    ]

