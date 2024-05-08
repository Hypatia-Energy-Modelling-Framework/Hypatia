# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 11:37:41 2023

@author: NAMAZIFN
"""


from hypatia import Model,Plotter, Sensitivity

#%%
test = Model(
    path = 'test/Trilateral/tests/test_storage/central_offshore_offshore_final/sets', 
    mode = 'Planning', period_step = 10, snapshot=True, MILP=True)
#%%
#test.create_data_excels(path = 'test/Trilateral/tests/test_LP/blue_hydrogen_final_LP/parameters_test',force_rewrite=True)
#%%
test.read_input_data(
    path = 'test/Trilateral/tests/test_storage/central_offshore_offshore_final/parameters'
)
#%%
test.resample_input_data(downsample=4)
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

# #%%
# import pandas as pd
# import os
# def dict_to_csv(Dict, path):
#     """Writes nested dicts  to csv"""

#     for key, value in Dict.items():
#         if isinstance(value, pd.DataFrame):
#             value.to_csv(f"{path}//{key}.csv",sep=",")
#         else:
#             new_path = f"{path}//{key}"
#             os.makedirs(new_path, exist_ok=True)
#             dict_to_csv(value, new_path)
#             #%%
# cost = test.results["variable_cost"]["reg1"]["Conversion"]
# #%%
# test.to_csv()
# #%%
# test._StrData.data["reg1"]["interest_rate"]

# #%%
# rate = 0.05
# step = 5
# import numpy as np
# import pandas as pd



# def var_cost(df,rate,step):
#     df = df.groupby(level=0).sum()
#     years = df.index.tolist()
#     Y = -1 * np.arange(len(years))*step
#     discount = np.power(1+rate, Y)
    
    
    
#     res = pd.DataFrame(index=df.index,columns=df.columns)
    
#     for idx,col in df.iteritems():
#         res.loc[col.index,idx] = col.values * discount
    
#     return res
# #%%

# a = var_cost(cost,0.05,5)


# #%%

# main_path = r"C:\Users\NAMAZIFN\OneDrive - VITO\Documents\GitHub\Hypatia\test\yeees_modified\blue_hydrogen\results_"

# reg_var = [
#     "variable_cost",
#     "fix_cost",
#     ]

# line_var = [
#     ""
#     ]

# #%%

# import pandas as pd
# import numpy as np
# #%%
# data = pd.read_excel(
#     'test/trilateral/tests/test_DS/central_offshore_offshore_final/parameters_new/parameters_reg1.xlsx',
#     sheet_name="capacity_factor_resource",
#     index_col=[0,1],
#     header=[0,1]
# )
# #%%
# import copy

# data_new = copy.deepcopy(data)

#%%
#data = data_new.groupby(by=np.arange(len(data.index.get_level_values(1)))//2,axis=0).mean()
# #%%
# Years = ["Y0","Y1"]
# #%%
# Timesteps = np.arange(4380).tolist()
# #%%
# data_gooz.index = pd.MultiIndex.from_product(
#     [Years, Timesteps],
#     names=["Years", "Timesteps"])
# #%%
# df = pd.DataFrame.from_dict(
#     {
#      'category': {0: 'Love', 1: 'Love', 2: 'Fashion', 3: 'Fashion', 4: 'Hair', 5: 'Movies', 6: 'Movies', 7: 'Health', 8: 'Health', 9: 'Celebs', 10: 'Celebs', 11: 'Travel', 12: 'Weightloss', 13: 'Diet', 14: 'Bags'}, 
#      'impressions': {0: 380, 1: 374242, 2: 197, 3: 13363, 4: 4, 5: 189, 6: 60632, 7: 269, 8: 40189, 9: 138, 10: 66590, 11: 2227, 12: 22668, 13: 21707, 14: 229}, 
#      'date': {0: '2013-11-04', 1: '2013-11-04', 2: '2013-11-04', 3: '2013-11-04', 4: '2013-11-04', 5: '2013-11-04', 6: '2013-11-04', 7: '2013-11-04', 8: '2013-11-04', 9: '2013-11-04', 10: '2013-11-04', 11: '2013-11-04', 12: '2013-11-04', 13: '2013-11-04', 14: '2013-11-04'}, 'cpc_cpm_revenue': {0: 0.36823, 1: 474.81522000000001, 2: 0.19434000000000001, 3: 18.264220000000002, 4: 0.00080000000000000004, 5: 0.23613000000000001, 6: 81.391139999999993, 7: 0.27171000000000001, 8: 51.258200000000002, 9: 0.11536, 10: 83.966859999999997, 11: 3.43248, 12: 31.695889999999999, 13: 28.459320000000002, 14: 0.43524000000000002}, 'clicks': {0: 0, 1: 183, 2: 0, 3: 9, 4: 0, 5: 1, 6: 20, 7: 0, 8: 21, 9: 0, 10: 32, 11: 1, 12: 12, 13: 9, 14: 2}, 'size': {0: '300x250', 1: '300x250', 2: '300x250', 3: '300x250', 4: '300x250', 5: '300x250', 6: '300x250', 7: '300x250', 8: '300x250', 9: '300x250', 10: '300x250', 11: '300x250', 12: '300x250', 13: '300x250', 14: '300x250'}
#     }
# )
# df.set_index(['date', 'category'], inplace=True)
# #%%
# df=df.groupby(by=["date","category"]).sum()
