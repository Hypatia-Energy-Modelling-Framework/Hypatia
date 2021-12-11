from hypatia import Model,Plotter

utopia = Model(
    path = 'sets', 
    mode = 'Operation' 
)

#utopia.create_data_excels(
#    path = 'parameters'
#)

utopia.read_input_data(
    path = 'parameters'
)

utopia.run(
    solver = 'scipy',
    verbosity = True,
)

utopia.to_csv(path='results')


# utopia.create_config_file(path=r'config.xlsx')

myplots = Plotter(utopia,config=r'config.xlsx',hourly_resolution= True)

# Sketching the hourly dispatch of the technologies for a given time horizom
myplots.plot_hourly_prod_by_tech(
    path = r'plots/dispatch.html',
    tech_group='Power Generation',
    regions = ['reg1','reg2'],
    year = 2021,
    start="01-01 00:00:00",
    end="01-03 23:00:00",
)

# Sketching the hourly dispatch of the technologies for the whole modelling period
myplots.plot_hourly_prod_by_tech(
    path = r'plots/full_dispatch.html',
    tech_group='Power Generation',
    regions = ['reg1','reg2'],
    year = 2021,
    start="01-01 00:00:00",
    end="12-29 23:00:00",
)

# Skething the prduction and consumption share of each technology including the imports and exports
myplots.plot_fuel_prod_cons(
    path = r'plots/prod_con_share.html',
    years = [2021],
    fuel_group = "Electricity",
    regions = ['reg1','reg2'],
    trade=True,
)

# Sketching the annual CO2-equivalent emissions
myplots.plot_emissions(
    path = r'plots/emissions.html',
    regions = ['reg1','reg2'],
    tech_group = 'Resource Extraction',
)