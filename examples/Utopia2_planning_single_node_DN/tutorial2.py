from hypatia import Model,Plotter

utopia = Model(
    path = 'sets', 
    mode = 'Planning' 
)

#utopia.create_data_excels(
#    path = r'parameters'
#)

utopia.read_input_data(
    path = r'parameters'
)

utopia.run(
    solver = 'scipy',
    verbosity = True,
)

utopia.to_csv(path='results')

#utopia.create_config_file(path=r'config.xlsx')

results = Plotter(utopia,config=r'config.xlsx',hourly_resolution=False)

# Sketching the new installed capacity of different technologies for given tech group
results.plot_new_capacity(
    path = r'plots/newcapacity.html',
    tech_group = 'Power Generation',
    regions = ['reg1'],
    cummulative=False,
)

# Sketching the total installed capacity of different technologies for given tech group (considering the decommissioned capacities)
results.plot_total_capacity(
    path = r'plots/totalcapacity.html',
    tech_group = 'Power Generation',
    regions = ['reg1'],
    kind="bar",
    decom_cap=True,
)

# Sketching the annual production of each technology
results.plot_prod_by_tech(
    tech_group ='Power Generation',
    regions = ['reg1'],
    path = r'plots/productionbytech.html',
)

# Sketching the annual production of each technology
results.plot_prod_by_tech(
    tech_group ='Refinery',
    regions = ['reg1'],
    path = r'plots/productionbytech_oil.html',
)

# Skething the prduction and consumption share of each technology including the imports and exports
results.plot_fuel_prod_cons(
    path = r'plots/prod_con_share.html',
    years = [2030],
    fuel_group = 'Electricity',
    regions = ['reg1'],
    trade=False,
)

# Skething the prduction and consumption share of each technology including the imports and exports
results.plot_fuel_prod_cons(
    path = r'plots/prod_con_share_oil.html',
    years = [2030],
    fuel_group = 'Fuel',
    regions = ['reg1'],
    trade=False,
)

# Sketching the annual CO2-equivalent emissions
results.plot_emissions(
    path = r'plots/emissions.html',
    regions = ['reg1'],
    tech_group = 'Resource Extraction',
)