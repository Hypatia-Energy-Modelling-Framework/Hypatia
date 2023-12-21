# -*- coding: utf-8 -*-
"""
Created on Wed Aug  9 16:23:48 2023

@author: NAMAZIFN
"""


from hypatia import Model,Plotter, Sensitivity

test = Model(
    path = 'test/yeees_modified/ammonia_import/sets', 
    mode = 'Planning', period_step = 5)

#%%
import pandas as pd
path = "test/yeees_modified/ammonia_import/parameters"
path2 = "test/yeees_modified/ammonia_import_snapshot_AD/parameters"

#%%

## Constants
years_to_drop = ["Y1","Y2"]

regional_sheets = ["V_OM","F_OM","INV","Decom_cost",
"Residual_capacity","Capacity_factor_tech","capacity_factor_resource","Specific_emission",
"Investment_taxsub","Fix_taxsub", "Carbon_tax","Min_newcap",
"Max_newcap","Min_totalcap","Max_totalcap","Min_production",
"Max_production","Min_production_h","Max_production_h",
"Emission_cap_annual","Demand"]


storage_sheets = ["Storage_min_SOC",
"Storage_charge_efficiency","Storage_discharge_efficiency"]

global_sheets = ["Max_production_global","Min_production_global","Glob_emission_cap_annual",
                 "Min_totalcap_global","Max_totalcal_global","Min_newcap_global","Max_newcap_global"]

connection_sheets = ["V_OM","Decom_cost",
"Line_efficiency","Residual_capacity","Capacity_factor_line",
"Min_newcap","Max_newcap","Min_totalcap","Max_totalcap"]

sizes = ["Cap_1", "Cap_2"]

for size in sizes:
    
    connection_sheets.append("F_OM_{}".format(size))
    connection_sheets.append("INV_{}".format(size))
    connection_sheets.append("Min_integer_cap_{}".format(size))
    
trade_data_ids = {
    "line_var_cost": {"sheet_name": "V_OM", "index_col": 0, "header": [0, 1]},
    "line_residual_cap": {
        "sheet_name": "Residual_capacity",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_eff": {"sheet_name": "Line_efficiency", "index_col": 0, "header": [0, 1]},
    "line_capacity_factor": {
        "sheet_name": "Capacity_factor_line",
        "index_col": 0,
        "header": [0, 1],
    },
    "annualprod_per_unitcapacity": {
        "sheet_name": "AnnualProd_perunit_capacity",
        "index_col": 0,
        "header": [0, 1],
    },
    
    "line_length": {
        "sheet_name": "Line_length",
        "index_col": 0,
        "header": [0, 1],
    },
"line_decom_cost": {
        "sheet_name": "Decom_cost",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_mintotcap": {
        "sheet_name": "Min_totalcap",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_maxtotcap": {
        "sheet_name": "Max_totalcap",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_min_newcap": {
        "sheet_name": "Min_newcap",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_max_newcap": {
        "sheet_name": "Max_newcap",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_lifetime": {
        "sheet_name": "Line_lifetime",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_economic_lifetime": {
        "sheet_name": "Line_Economic_life",
        "index_col": 0,
        "header": [0, 1],
    },
    "interest_rate": {
        "sheet_name": "Interest_rate",
        "index_col": 0,
        "header": [0, 1],
    },
}

trade_data_ids_to_change = {
    "line_var_cost": {"sheet_name": "V_OM", "index_col": 0, "header": [0, 1]},
    "line_residual_cap": {
        "sheet_name": "Residual_capacity",
        "index_col": 0,
        "header": [0, 1],
    },
    "line_eff": {"sheet_name": "Line_efficiency", "index_col": 0, "header": [0, 1]},
    "line_capacity_factor": {
        "sheet_name": "Capacity_factor_line",
        "index_col": 0,
        "header": [0, 1],
    },
        "line_decom_cost": {
                "sheet_name": "Decom_cost",
                "index_col": 0,
                "header": [0, 1],
            },
            "line_mintotcap": {
                "sheet_name": "Min_totalcap",
                "index_col": 0,
                "header": [0, 1],
            },
            "line_maxtotcap": {
                "sheet_name": "Max_totalcap",
                "index_col": 0,
                "header": [0, 1],
            },
            "line_min_newcap": {
                "sheet_name": "Min_newcap",
                "index_col": 0,
                "header": [0, 1],
            },
            "line_max_newcap": {
                "sheet_name": "Max_newcap",
                "index_col": 0,
                "header": [0, 1],
            }}

global_data_ids = {
    "global_min_production": {
        "sheet_name": "Min_production_global",
        "index_col": 0,
        "header": 0,
    },
    "global_max_production": {
        "sheet_name": "Max_production_global",
        "index_col": 0,
        "header": 0,
    },
    "global_emission_cap_annual": {
        "sheet_name": "Glob_emission_cap_annual",
        "index_col": 0,
        "header": 0,
    },

    "global_mintotcap": {
        "sheet_name": "Min_totalcap_global",
        "index_col": 0,
        "header": 0,
    },
    "global_maxtotcap": {
        "sheet_name": "Max_totalcap_global",
        "index_col": 0,
        "header": 0,
    },
    "global_min_newcap": {
        "sheet_name": "Min_newcap_global",
        "index_col": 0,
        "header": 0,
    },
    "global_max_newcap": {
        "sheet_name": "Max_newcap_global",
        "index_col": 0,
        "header": 0,
    },
    "global_discount_rate": {
        "sheet_name": "Discount_rate",
        "index_col": 0,
        "header": 0,
    },
}


for size in sizes:
    
    trade_data_ids.update(
        {"line_fixed_cost_{}".format(size): {"sheet_name": "F_OM_{}".format(size), "index_col": 0, "header": [0, 1]},
         "line_inv_{}".format(size): {"sheet_name": "INV_{}".format(size), "index_col": 0, "header": [0, 1]},
                     "line_integer_cap_{}".format(size) : {"sheet_name": "Min_integer_cap_{}".format(size), "index_col": 0, "header": [0,1]
            }})
    
    trade_data_ids_to_change.update(
        {"line_fixed_cost_{}".format(size): {"sheet_name": "F_OM_{}".format(size), "index_col": 0, "header": [0, 1]},
         "line_inv_{}".format(size): {"sheet_name": "INV_{}".format(size), "index_col": 0, "header": [0, 1]},
                     "line_integer_cap_{}".format(size) : {"sheet_name": "Min_integer_cap_{}".format(size), "index_col": 0, "header": [0,1]
            }})
    

regional_data_ids = {}
regional_data_ids_to_change = {}
for reg in test._StrData.regions:
    regional_data_ids[reg] = {
        "tech_fixed_cost": {"sheet_name": "F_OM", "index_col": 0, "header": [0, 1]},
        "tech_var_cost": {"sheet_name": "V_OM", "index_col": [0,1], "header": [0, 1]},
        "tech_residual_cap": {
            "sheet_name": "Residual_capacity",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_max_production": {
            "sheet_name": "Max_production",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_min_production": {
            "sheet_name": "Min_production",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_max_production_h": {
            "sheet_name": "Max_production_h",
            "index_col": [0, 1],
            "header": [0, 1],
        },
        "tech_min_production_h": {
            "sheet_name": "Min_production_h",
            "index_col": [0, 1],
            "header": [0, 1],
        },
        "annualprod_per_unitcapacity": {
            "sheet_name": "AnnualProd_perunit_capacity",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_efficiency": {
            "sheet_name": "Tech_efficiency",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_capacity_factor": {
            "sheet_name": "Capacity_factor_tech",
            "index_col": 0,
            "header": [0, 1],
        },
        "specific_emission": {
            "sheet_name": "Specific_emission",
            "index_col": 0,
            "header": [0, 1],
        },
        "carbon_tax": {
            "sheet_name": "Carbon_tax",
            "index_col": 0,
            "header": [0, 1],
        },
        "fix_taxsub": {
            "sheet_name": "Fix_taxsub",
            "index_col": 0,
            "header": [0, 1, 2],
        },
        "demand": {"sheet_name": "Demand", "index_col": [0, 1], "header": 0},
        "res_capacity_factor": {
            "sheet_name": "capacity_factor_resource",
            "index_col": [0, 1],
            "header": [0, 1],
        },
        "emission_cap_annual": {
            "sheet_name": "Emission_cap_annual",
            "index_col": 0,
            "header": 0,
        },
        
        "tech_inv": {"sheet_name": "INV", "index_col": 0, "header": [0, 1]},
        "tech_decom_cost": {
            "sheet_name": "Decom_cost",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_mintotcap": {
            "sheet_name": "Min_totalcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_maxtotcap": {
            "sheet_name": "Max_totalcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_min_newcap": {
            "sheet_name": "Min_newcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_max_newcap": {
            "sheet_name": "Max_newcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_lifetime": {
            "sheet_name": "Tech_lifetime",
            "index_col": 0,
            "header": [0, 1],
        },
        "economic_lifetime": {
            "sheet_name": "Economic_lifetime",
            "index_col": 0,
            "header": [0, 1],
        },
        "interest_rate": {
            "sheet_name": "Interest_rate",
            "index_col": 0,
            "header": [0, 1],
        },
        "inv_taxsub": {
            "sheet_name": "Investment_taxsub",
            "index_col": 0,
            "header": [0, 1, 2],
        },
        "discount_rate": {
            "sheet_name": "Discount_rate",
            "index_col": 0,
            "header": 0,
        },
    }
    
    regional_data_ids_to_change[reg] = {
        "tech_fixed_cost": {"sheet_name": "F_OM", "index_col": 0, "header": [0, 1]},
        "tech_var_cost": {"sheet_name": "V_OM", "index_col": [0,1], "header": [0, 1]},
        "tech_residual_cap": {
            "sheet_name": "Residual_capacity",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_max_production": {
            "sheet_name": "Max_production",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_min_production": {
            "sheet_name": "Min_production",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_max_production_h": {
            "sheet_name": "Max_production_h",
            "index_col": [0, 1],
            "header": [0, 1],
        },
        "tech_min_production_h": {
            "sheet_name": "Min_production_h",
            "index_col": [0, 1],
            "header": [0, 1],
        },
        
        "tech_efficiency": {
            "sheet_name": "Tech_efficiency",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_capacity_factor": {
            "sheet_name": "Capacity_factor_tech",
            "index_col": 0,
            "header": [0, 1],
        },
        "specific_emission": {
            "sheet_name": "Specific_emission",
            "index_col": 0,
            "header": [0, 1],
        },
        "carbon_tax": {
            "sheet_name": "Carbon_tax",
            "index_col": 0,
            "header": [0, 1],
        },
        "fix_taxsub": {
            "sheet_name": "Fix_taxsub",
            "index_col": 0,
            "header": [0, 1, 2],
        },
        "demand": {"sheet_name": "Demand", "index_col": [0, 1], "header": 0},
        "res_capacity_factor": {
            "sheet_name": "capacity_factor_resource",
            "index_col": [0, 1],
            "header": [0, 1],
        },
        "emission_cap_annual": {
            "sheet_name": "Emission_cap_annual",
            "index_col": 0,
            "header": 0,
        },
        
        "tech_inv": {"sheet_name": "INV", "index_col": 0, "header": [0, 1]},
        "tech_decom_cost": {
            "sheet_name": "Decom_cost",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_mintotcap": {
            "sheet_name": "Min_totalcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_maxtotcap": {
            "sheet_name": "Max_totalcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_min_newcap": {
            "sheet_name": "Min_newcap",
            "index_col": 0,
            "header": [0, 1],
        },
        "tech_max_newcap": {
            "sheet_name": "Max_newcap",
            "index_col": 0,
            "header": [0, 1],
        },

        "inv_taxsub": {
            "sheet_name": "Investment_taxsub",
            "index_col": 0,
            "header": [0, 1, 2],
        },
        "discount_rate": {
            "sheet_name": "Discount_rate",
            "index_col": 0,
            "header": 0,
        },
    }

    if "Storage" in test._StrData.Technologies[reg].keys():
    
        regional_data_ids[reg].update(
            {
                "storage_charge_efficiency": {
                    "sheet_name": "Storage_charge_efficiency",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_discharge_efficiency": {
                    "sheet_name": "Storage_discharge_efficiency",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_min_SOC": {
                    "sheet_name": "Storage_min_SOC",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_initial_SOC": {
                    "sheet_name": "Storage_initial_SOC",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_charge_time": {
                    "sheet_name": "Storage_charge_time",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_discharge_time": {
                    "sheet_name": "Storage_discharge_time",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_max_discharge": {
                    "sheet_name": "Storage_max_discharge",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_max_charge": {
                    "sheet_name": "Storage_max_charge",
                    "index_col": 0,
                    "header": 0,
                },
            }
        )
        

        regional_data_ids_to_change[reg].update(
            {
                "storage_charge_efficiency": {
                    "sheet_name": "Storage_charge_efficiency",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_discharge_efficiency": {
                    "sheet_name": "Storage_discharge_efficiency",
                    "index_col": 0,
                    "header": 0,
                },
                "storage_min_SOC": {
                    "sheet_name": "Storage_min_SOC",
                    "index_col": 0,
                    "header": 0,
                },

            }
        )
#%%

## Changing the parameters_connection sheets

    
connection_data = {}
connection_data_new = {}
for key, value in trade_data_ids.items():
    
    connection_data[key] = pd.read_excel(
        r"{}/parameters_connections.xlsx".format(path),
        sheet_name=value["sheet_name"],
        index_col=value["index_col"],
        header=value["header"],)
    
    if key in trade_data_ids_to_change.keys():
        connection_data_new[key] = connection_data[key].drop(years_to_drop)
        connection_data_new[key].rename(index={"Y3":"Y1"}, inplace=True)
        
    else:
        
        connection_data_new[key] = connection_data[key]
    
#%%  

## Writing the parameter_connection file
with pd.ExcelWriter(
    r"{}/parameters_connections.xlsx".format(path2)
) as writer:

    for key, value in connection_data_new.items():

        value.to_excel(writer, sheet_name=trade_data_ids[key]["sheet_name"])
        
        
#%%

## Changing the parameters_global file
    
global_data = {}
global_data_new = {}
for key, value in global_data_ids.items():
    
    global_data[key] = pd.read_excel(
        r"{}/parameters_global.xlsx".format(path),
        sheet_name=value["sheet_name"],
        index_col=value["index_col"],
        header=value["header"],)
    
    global_data_new[key] = global_data[key].drop(years_to_drop)
    global_data_new[key].rename(index={"Y3":"Y1"}, inplace=True)

#%%

## Writing the parameter_global file

with pd.ExcelWriter(
    r"{}/parameters_global.xlsx".format(path2)
) as writer:

    for key, value in global_data_new.items():

        value.to_excel(writer, sheet_name=global_data_ids[key]["sheet_name"])
        
#%%
        
## Changing the regional parameters

regional_data = {}
regional_data_new = {}
for reg in test._StrData.regions:
    
    regional_data_= {}
    regional_data_new_ = {}
    
    for key, value in regional_data_ids[reg].items():
        
        regional_data_[key] = pd.read_excel(
            r"{}/parameters_{}.xlsx".format(path,reg),
            sheet_name=value["sheet_name"],
            index_col=value["index_col"],
            header=value["header"],)
        
        if key in regional_data_ids_to_change[reg]:
            regional_data_new_[key] = regional_data_[key].drop(years_to_drop)
            regional_data_new_[key].rename(index={"Y3":"Y1"}, inplace=True)
        
        else:
            
            regional_data_new_[key] = regional_data_[key]
            
    
    regional_data[reg] = regional_data_
    regional_data_new[reg] = regional_data_new_

#%%

## Writing the parameter_reg files

for reg in test._StrData.regions:

    with pd.ExcelWriter(r"{}/parameters_{}.xlsx".format(path2, reg)) as writer:

        for key, value in regional_data_new[reg].items():


            value.to_excel(writer, sheet_name=regional_data_ids[reg][key]["sheet_name"])

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        