import pandas as pd
import numpy as np
from abc import abstractmethod

class ExampleSettings:
    @property
    @abstractmethod
    def global_settings(self):
        pass

    @property
    @abstractmethod
    def regional_settings(self):
        pass

class Utopia2PlanningSingleNodeDN(ExampleSettings):
    @property
    def global_settings(self):
        return {
            "Regions": pd.DataFrame(
                np.array([['reg1', 'Utopia']]),
                columns=["Region", "Region_name"],
            ),
            "Years": pd.DataFrame(
                np.array([
                    ['Y0', '2020'],
                    ['Y1', '2021'],
                    ['Y2', '2022'],
                    ['Y3', '2023'],
                    ['Y4', '2024'],
                    ['Y5', '2025'],
                    ['Y6', '2026'],
                    ['Y7', '2027'],
                    ['Y8', '2028'],
                    ['Y9', '2029'],
                    ['Y10', '2030'],
                ]),
                columns=["Year", "Year_name"],
            ),
            "Technologies_glob": pd.DataFrame(
                np.array([
                    ['Oil_extr', 'Oil Resource Extraction', "Supply", "extraction units", "Kilo barrels of oil"],
                    ['Oil_refine', 'Oil Refinery', "Conversion", "kb/d", "Kilo barrels of oil"],
                    ['Oil_PP', 'Oil Power Plant', "Conversion", "GW", "GWh"],
                    ['Hydro_PP', 'Hydro Power Plant', "Supply", "GW", "GWh"],
                    ['Elec_transmission', 'Electricity Transmission', 'Transmission', "GW", "GWh"],
                    ['Diesel_pipeline', 'Diesel Pipeline', "Transmission", "kb/y", "Kilo barrels of oil"],
                    ['EV', 'Electric Vehicles Demand', "Demand", "GWh", "GWh"],
                    ['ICEV', 'ICE Vehicles Demand', "Demand", "GWh", "GWh"],
                    ['HH_elec_demand', 'Household Elecricity Demand', "Demand", "-", "-"],
                    ['Other_elec_demand', 'Other Electricity Demand', "Demand", "-", "-"],
                ]),
                columns=["Technology", "Tech_name", "Tech_category", "Tech_cap_unit", "Tech_act_unit"]
            ),
            "Carriers_glob": pd.DataFrame(
                np.array([
                    ['Raw_oil', 'Raw Oil', "Resource", "Kilo barrels of oil"],
                    ['Oil', 'Oil', "Intermediate", "Kilo barrels of oil"],
                    ['Elec', 'Electricity', "Intermediate", "GWh"],
                    ['Oil_final', 'Final Diesel Oil', "Demand", "Kilo barrels of oil"],
                    ['Elec_final', 'Final Electricity', "Demand", "GWh"],
                ]),
                columns=["Carrier", "Carr_name", "Carr_type", "Carr_unit"]
            ),
            "Timesteps": pd.DataFrame(
                np.array([
                    ['WD_days', 'Weekdays-days', '0.357534246575342'],
                    ['WD_nights', 'Weekdays-nights', '0.357534246575342'],
                    ['WE_days', 'Weekends-days', '0.142465753424658'],
                    ['WE_nights', 'Weekends-nights', '0.142465753424658'],

                ]),
                columns=["Timeslice", "Timeslice_name", "Timeslice_fraction"]
            ),

            "Emissions": pd.DataFrame(
                np.array([['CO2', 'CO2 emissions', 'ton']]),
                columns=["Emission", "Emission_name", "Emission_unit"],
            ),
        }

    @property
    def regional_settings(self):
        return {
            'reg1': {
                "Technologies": pd.DataFrame(
                    np.array([
                        ['Oil_extr', 'Oil Resource Extraction', "Supply"],
                        ['Oil_refine', 'Oil Refinery', "Conversion"],
                        ['Oil_PP', 'Oil Power Plant', "Conversion"],
                        ['Hydro_PP', 'Hydro Power Plant', "Supply"],
                        ['Elec_transmission', 'Electricity Transmission', 'Transmission'],
                        ['Diesel_pipeline', 'Diesel Pipeline', "Transmission"],
                        ['EV', 'Electric Vehicles Demand', "Demand"],
                        ['ICEV', 'ICE Vehicles Demand', "Demand"],
                        ['HH_elec_demand', 'Household Elecricity Demand', "Demand"],
                        ['Other_elec_demand', 'Other Electricity Demand', "Demand"],
                    ]),
                    columns=["Technology", "Tech_name", "Tech_category"]
                ),
                "Carriers": pd.DataFrame(
                    np.array([
                        ['Raw_Oil', 'Raw Oil', "Resource"],
                        ['Oil', 'Oil', "Intermediate"],
                        ['Elec', 'Electricity', "Intermediate"],
                        ['Oil_final', 'Final Diesel Oil', "Demand"],
                        ['Elec_final', 'Final Electricity', "Demand"],
                    ]),
                    columns=["Carrier", "Carr_name", "Carr_type"]
                ),
                "Carrier_input": pd.DataFrame(
                    np.array([
                        ['Oil_refine', 'Raw_Oil'],
                        ['Oil_PP', 'Oil'],
                        ['Elec_transmission', 'Elec'],
                        ['Diesel_pipeline', 'Oil'],
                        ['EV', 'Elec_final'],
                        ['ICEV', 'Oil_final'],
                        ['HH_elec_demand', 'Elec_final'],
                        ['Other_elec_demand', 'Elec_final'],
                    ]),
                    columns=["Technology", "Carrier_in"]
                ),
                "Carrier_output": pd.DataFrame(
                    np.array([
                        ['Oil_extr', 'Raw_Oil'],
                        ['Oil_refine', 'Oil'],
                        ['Oil_PP', 'Elec'],
                        ['Hydro_PP', 'Elec'],
                        ['Elec_transmission', 'Elec_final'],
                        ['Diesel_pipeline', 'Oil_final'],
                    ]),
                    columns=["Technology", "Carrier_out"]
                ),
            }
        }

class Utopia2OperationMultiNode(ExampleSettings):
    @property
    def global_settings(self):
        global_settings = {
            "Regions": pd.DataFrame(
                np.array([
                    ['reg1', 'Utopia_north'],
                    ['reg2', 'Utopia_south']
                ]),
                columns=["Region", "Region_name"],
            ),
            "Years": pd.DataFrame(
                np.array([
                    ['Y0', '2021'],
                ]),
                columns=["Year", "Year_name"],
            ),
            "Technologies_glob": pd.DataFrame(
                np.array([
                    ["NG_extraction", "Natural Gas Extraction",	"Supply", "number of extraction units", "BOE"],
                    ["CHP_PP", "Combined Heat and Power", "Conversion_plus", "MW", "MWh"],
                    ["Geo_PP", "Geothermal Power Plant", "Supply", "MW", "MWh"],
                    ["Solar_PP", "Solar Power Plant", "Supply", "MW", "MWh"],
                    ["Wind_PP", "Wind Power Plant", "Supply", "MW", "MWh"],
                    ["Hydro_PP", "Hydro Power Plant", "Supply", "MW", "MWh"],
                    ["Elec_transmission", "Electricity Transmission", "Transmission", "MW", "MWh"],
                    ["Gas_pipeline", "Natural Gas Pipeline", "Transmission", "MW", "MWh"],
                    ["Boiler", "Gas Boiler", "Conversion", "number of boilers", "MWh"],
                    ["Elec_demand", "Final Electricity Demand", "Demand", "-", "-"],
                    ["Heat_demand", "Final Heat Demand", "Demand", "-", "-"],
                ]),
                columns=["Technology", "Tech_name", "Tech_category", "Tech_cap_unit", "Tech_act_unit"]
            ),
            "Carriers_glob": pd.DataFrame(
                np.array([
                    ['NG', 'Fuel Natural Gas', "Resource", "BOE"],
                    ['Elec', 'Electricity', "Intermediate", "MWh"],
                    ['Elec_final', 'Final Electricity', "Demand", "MWh"],
                    ['Gas_final', 'Final Gas', "Intermediate", "BOE"],
                    ['Heat', 'Heat', "Demand", "MWh"],
                ]),
                columns=["Carrier", "Carr_name", "Carr_type", "Carr_unit"]
            ),
            "Emissions": pd.DataFrame(
                np.array([['CO2', 'CO2 emissions', 'ton']]),
                columns=["Emission", "Emission_name", "Emission_unit"],
            ),
        }

        time_slices = []
        for i in range(1, 8761):
            time_slices.append([str(i), "h"+str(i), 0.000114155251141553])

        global_settings["Timesteps"] = pd.DataFrame(
            np.array(time_slices),
            columns=["Timeslice", "Timeslice_name", "Timeslice_fraction"]
        )

        return global_settings

    @property
    def regional_settings(self):
        return {
            'reg1': {
                "Technologies": pd.DataFrame(
                    np.array([
                        ["NG_extraction", "Natural Gas Extraction",	"Supply"],
                        ["CHP_PP", "Combined Heat and Power", "Conversion_plus"],
                        ["Wind_PP", "Wind Power Plant", "Supply"],
                        ["Hydro_PP", "Hydro Power Plant", "Supply"],
                        ["Elec_transmission", "Electricity Transmission", "Transmission"],
                        ["Gas_pipeline", "Natural Gas Pipeline", "Transmission"],
                        ["Boiler", "Gas Boiler", "Conversion"],
                        ["Elec_demand", "Final Electricity", "Demand"],
                        ["Heat_demand", "Final Heat", "Demand"],
                    ]),
                    columns=["Technology", "Tech_name", "Tech_category"]
                ),
                "Carriers": pd.DataFrame(
                    np.array([
                        ['NG', 'Fuel Natural Gas', "Resource"],
                        ['Elec', 'Electricity', "Intermediate"],
                        ['Elec_final', 'Final Electricity', "Demand"],
                        ['Gas_final', 'Final Gas', "Intermediate"],
                        ['Heat', 'Heat', "Demand"],
                    ]),
                    columns=["Carrier", "Carr_name", "Carr_type"]
                ),
                "Carrier_input": pd.DataFrame(
                    np.array([
                        ['CHP_PP', 'NG'],
                        ['Elec_transmission', 'Elec'],
                        ['Gas_pipeline', 'NG'],
                        ['Boiler', 'Gas_final'],
                        ['Elec_demand', 'Elec_final'],
                        ['Heat_demand', 'Heat'],
                    ]),
                    columns=["Technology", "Carrier_in"]
                ),
                "Carrier_output": pd.DataFrame(
                    np.array([
                        ['NG_extraction', 'NG'],
                        ['CHP_PP', 'Elec'],
                        ['CHP_PP', 'Heat'],
                        ['Wind_PP', 'Elec'],
                        ['Hydro_PP', 'Elec'],
                        ['Elec_transmission', 'Elec_final'],
                        ['Gas_pipeline', 'Gas_final'],
                        ['Boiler', 'Heat'],

                    ]),
                    columns=["Technology", "Carrier_out"]
                ),
            },
            'reg2': {
                "Technologies": pd.DataFrame(
                    np.array([
                        ["Geo_PP", "Geothermal Power Plant", "Supply"],
                        ["Solar_PP", "Solar Power Plant", "Supply"],
                        ["Elec_transmission", "Electricity Transmission", "Transmission"],
                        ["Elec_demand", "Final Electricity", "Demand"],
                    ]),
                    columns=["Technology", "Tech_name", "Tech_category"]
                ),
                "Carriers": pd.DataFrame(
                    np.array([
                        ['Elec', 'Electricity', "Intermediate"],
                        ['Elec_final', 'Final Electricity', "Demand"],
                    ]),
                    columns=["Carrier", "Carr_name", "Carr_type"]
                ),
                "Carrier_input": pd.DataFrame(
                    np.array([
                        ['Elec_transmission', 'Elec'],
                        ['Elec_demand', 'Elec_final'],
                    ]),
                    columns=["Technology", "Carrier_in"]
                ),
                "Carrier_output": pd.DataFrame(
                    np.array([
                        ['Geo_PP', 'Elec'],
                        ['Solar_PP', 'Elec'],
                        ['Elec_transmission', 'Elec_final'],
                    ]),
                    columns=["Technology", "Carrier_out"]
                ),
            }
        }
