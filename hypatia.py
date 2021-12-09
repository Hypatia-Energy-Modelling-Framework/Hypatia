# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# Importing the Hypatia model
from hypatia import Model

#%%

# Initializing the Hypatia model by reading the excel-based set files
model = Model(path = r'', mode = 'Operation' )

#%%
# Creating the excel-based parameter files
model.create_data_excels(path = r'')
#%%
# Reading the input data
model.read_input_data(path = r'')
#%%
# Running the model
model.run(solver = 'scipy', verbosity = True,force_rewrite=True)
#%%
# Exporting the raw results to csv files
model.to_csv(path=r'/results',force_rewrite = True)
#%%
# Creating a confuguration excel file to be filled by the user for the output plots
model.create_config_file(path=r'/config.xlsx')
#%%
# Import the plotting tool of the Hypatia model
from hypatia import Plotter
#%%
# Initializing the built-in plotter class
plots = Plotter(model,config=r'/config.xlsx',hourly_resolution= True)
#%%
# Sketching the new installed capacity of different technologies for given tech group
plots.plot_new_capacity(
    path=r"/newcapacity.html",
    tech_group="Power Generation",
    regions=["reg1"],
    kind="bar",
    cummulative=False,
    mode="updatemenus",
    aggregate=False,
)

#%%
# Sketching the total installed capacity of different technologies for given tech group (considering the decommissioned capacities)
plots.plot_total_capacity(
    path=r"/totalcapacity.html",
    tech_group="Power Generation",
    regions=["reg1"],
    kind="bar",
    decom_cap=True,
    mode="updatemenus",
    aggregate=False,
)

#%%
# Sketching the hourly dispatch of the technologies for a given time horizom
plots.plot_hourly_prod_by_tech(path = r'/dispatch.html',
                                 tech_group='Power Generation',
                                 regions = ['reg1'],
                                 year = 2021,
                                 kind = 'area',
                                 freq = 'h',
                                start="01-01 00:00:00",
                                end="01-03 23:00:00",
                                mode="updatemenus",
                                aggregate=False,)

#%%
# Sketching the hourly dispatch of the technologies for the whole modelling period
plots.plot_hourly_prod_by_tech(path = r'/full_dispatch.html',
                                 tech_group='Power Generation',
                                 regions = ['reg1'],
                                 year = 2021,
                                 kind = 'area',
                                 freq = 'h',
                                start="01-01 00:00:00",
                                end="12-29 23:00:00",
                                mode="updatemenus",
                                aggregate=False,)

#%%
plots.plot_prod_by_tech(tech_group='Power Generation',regions = ['reg1'],
                          path = r'/prod_by_tech.html',
                          kind = 'bar')


#%%
# Skething the prduction and consumption share of each technology including the imports and exports
plots.plot_fuel_prod_cons(path = r'/prod_con_share.html',
        years = [2021],
        fuel_group = "Electricity",
        regions = ['reg1'],
        kind="pie",
        trade=True,
        mode="updatemenus",
        aggregate=False,)
#%%
# Sketching the annual CO2-equivalent emissions
plots.plot_emissions(path = r'/emissions.html',
        regions = ['reg1'],
        tech_group = 'Resource Extraction',
        kind="bar",
        mode="updatemenus",
        aggregate=False,)