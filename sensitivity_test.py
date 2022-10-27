# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 15:45:44 2022

@author: NAMAZIFN
"""
###########################################
#Running the model with the baseline data#
###########################################

from hypatia import Model,Plotter,Sensitivity
#%%
Belgium = Model(
    path = 'test/final_case/sets', 
    mode = 'Planning' 
)
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
# Belgium.to_csv(path='test/final_case/results_baseline')
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
sensitivity_1.run_sensitivity(solver='scipy',force_rewrite=True,path='test/final_case/all_results_N2_final')
#%%
from behyfe_plot import HyPlot
#%%
plots_negar = HyPlot(Belgium, 
                     results_path = r'C:/Users/NAMAZIFN/OneDrive - VITO/Documents/GitHub/Hypatia/test/final_case/all_results_N2_final', 
                     config = r'test/final_case/config.xlsx', sample_N=2, hourly_resolution=False,sens=sensitivity_1)

#%%
plots_negar.plot_total_capacity(path = r'test/final_case/plots/totalcapacity_N2_final.html',
                                tech_group = 'hydrogen supply',
                                )

#%%
years = plots_negar.years
years_new = plots_negar.years_new
#%%
samples = sensitivity_1._sample
#%%
parameter1 = sensitivity_1._parameters[0].name