import pandas as pd
import numpy as np
import unittest
import copy
from hypatia.backend.ModelSettings import ModelSettings
from hypatia.utility.constants import ModelMode
from hypatia.examples.ExampleSettings import (
    Utopia2PlanningSingleNodeDN,
    Utopia2OperationMultiNode
)
import hypatia.error_log.Exceptions as hypatiaException

'''
Unit tests for the functions in ModelSettings.py
'''

class TestModelSettings(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestModelSettings, self).__init__(*args, **kwargs)
        self.single_node = Utopia2PlanningSingleNodeDN()
        self.multi_node = Utopia2OperationMultiNode()

    """
    Init tests

    Test the ModelSettings initialization logic
    """
    def test_single_node_planning_settings(self):
        ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )

    def test_single_node_operation_settings(self):
        self.assertRaises(
            hypatiaException.WrongNumberOfYears,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.single_node.global_settings,
                self.single_node.regional_settings,
            )
        )

    def test_multi_node_planning_settings(self):
        ModelSettings(
            ModelMode.Planning,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )

    def test_multi_node_planning_operation(self):
        ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )

    # TODO(afa) We do not verify this in a good way. Improve code to check for missing tables
    # def test_global_settings_missing_table(self):
    #     global_settings = copy.deepcopy(self.single_node.global_settings)
    #     global_settings.pop('Regions', None)
    #     self.assertRaises(
    #         KeyError,
    #         lambda: ModelSettings(
    #             ModelMode.Planning,
    #             global_settings,
    #             self.single_node.regional_settings,
    #         )
    #     )

    def test_global_settings_wrong_table(self):
        # single node
        global_settings = copy.deepcopy(self.single_node.global_settings)
        global_settings["wrong_table"] = pd.DataFrame(
            np.array([['data', 'data 1']]),
            columns=["column", "column 1"],
        ),
        self.assertRaises(
            hypatiaException.WrongTableName,
            lambda: ModelSettings(
                ModelMode.Planning,
                global_settings,
                self.single_node.regional_settings,
            )
        )

        # multi node
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings["wrong_table"] = pd.DataFrame(
            np.array([['data', 'data 1']]),
            columns=["column", "column 1"],
        ),
        self.assertRaises(
            hypatiaException.WrongTableName,
            lambda: ModelSettings(
                ModelMode.Operation,
                global_settings,
                self.multi_node.regional_settings,
            )
        )


    def test_global_settings_wrong_table_index(self):
        # single node
        global_settings = copy.deepcopy(self.single_node.global_settings)
        global_settings["Regions"].columns = ["Wrong_Column_name", "Region_name"]
        self.assertRaises(
            hypatiaException.WrongIndex,
            lambda: ModelSettings(
                ModelMode.Planning,
                global_settings,
                self.single_node.regional_settings,
            )
        )

        # multi node
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings["Regions"].columns = ["Wrong_Column_name", "Region_name"]
        self.assertRaises(
            hypatiaException.WrongIndex,
            lambda: ModelSettings(
                ModelMode.Operation,
                global_settings,
                self.multi_node.regional_settings,
            )
        )


    def test_global_settings_with_nan(self):
        # single node
        global_settings = copy.deepcopy(self.single_node.global_settings)
        global_settings["Regions"] = global_settings["Regions"].append(
            {"Region": "reg2"},
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.NanValues,
            lambda: ModelSettings(
                ModelMode.Planning,
                global_settings,
                self.single_node.regional_settings,
            )
        )

        # multi node
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings["Regions"] = global_settings["Regions"].append(
            {"Region": "reg3"},
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.NanValues,
            lambda: ModelSettings(
                ModelMode.Operation,
                global_settings,
                self.multi_node.regional_settings,
            )
        )


    def test_global_settings_wrong_technology_category(self):
        # single node
        global_settings = copy.deepcopy(self.single_node.global_settings)
        global_settings["Technologies_glob"] = global_settings["Technologies_glob"].append(
            {
                "Technology": 'Hydro_PP',
                "Tech_name": 'Hydro Power Plant',
                "Tech_category":  "Wrong category ",
                "Tech_cap_unit": "GW",
                "Tech_act_unit": "GWh"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongTechCategory,
            lambda: ModelSettings(
                ModelMode.Planning,
                global_settings,
                self.single_node.regional_settings,
            )
        )

        # multi node
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings["Technologies_glob"] = global_settings["Technologies_glob"].append(
            {
                "Technology": 'Hydro_PP',
                "Tech_name": 'Hydro Power Plant',
                "Tech_category":  "Wrong category ",
                "Tech_cap_unit": "GW",
                "Tech_act_unit": "GWh"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongTechCategory,
            lambda: ModelSettings(
                ModelMode.Operation,
                global_settings,
                self.multi_node.regional_settings,
            )
        )

    def test_global_settings_wrong_carrier_type(self):
        # single node
        global_settings = copy.deepcopy(self.single_node.global_settings)
        global_settings["Carriers_glob"] = global_settings["Carriers_glob"].append(
            {
                "Carrier": 'Raw oil',
                "Carr_name": 'Raw Oil',
                "Carr_type":  "Wrong resource type",
                "Carr_unit": "Kilo barrels of oil"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongCarrierType,
            lambda: ModelSettings(
                ModelMode.Planning,
                global_settings,
                self.single_node.regional_settings,
            )
        )

         # multi node
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings["Carriers_glob"] = global_settings["Carriers_glob"].append(
            {
                "Carrier": 'Raw oil',
                "Carr_name": 'Raw Oil',
                "Carr_type":  "Wrong resource type",
                "Carr_unit": "Kilo barrels of oil"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongCarrierType,
            lambda: ModelSettings(
                ModelMode.Operation,
                global_settings,
                self.multi_node.regional_settings,
            )
        )

    # TODO(afa) We do not verify this in a good way. Improve code to check for missing tables
    # def test_regional_settings_missing_table(self):
    #     regional_settings = copy.deepcopy(self.single_node.regional_settings)
    #     regional_settings['reg1'].pop('Carrier_input', None)
    #     self.assertRaises(
    #         KeyError,
    #         lambda: ModelSettings(
    #             ModelMode.Planning,
    #             self.single_node.global_settings,
    #             self.single_node.regional_settings,
    #         )
    #     )

    def test_regional_settings_wrong_table(self):
        #single node
        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings['reg1']["wrong_table"] = pd.DataFrame(
            np.array([['data', 'data 1']]),
            columns=["column", "column 1"],
        ),
        self.assertRaises(
            hypatiaException.WrongTableName,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        #multi node
        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings['reg2']["wrong_table"] = pd.DataFrame(
            np.array([['data', 'data 1']]),
            columns=["column", "column 1"],
        ),
        self.assertRaises(
            hypatiaException.WrongTableName,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )


    def test_regional_settings_wrong_table_index(self):
        #single node
        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Carriers"].columns = ["Carrier", "Wrong column name", "Carr_type"]
        self.assertRaises(
            hypatiaException.WrongIndex,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        #multi node
        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Carriers"].columns = ["Carrier", "Wrong column name", "Carr_type"]
        self.assertRaises(
            hypatiaException.WrongIndex,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )


    def test_regional_settings_with_nan(self):
        #single node
        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Carriers"] = regional_settings["reg1"]["Carriers"].append(
            {"Carrier": "Some carrier"},
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.NanValues,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        #multi node
        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Carriers"] = regional_settings["reg2"]["Carriers"].append(
            {"Carrier": "Some carrier"},
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.NanValues,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )

    def test_regional_settings_wrong_technology_category(self):
        #single node
        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Technologies"] = regional_settings["reg1"]["Technologies"].append(
            {
                "Technology": 'Hydro_PP',
                "Tech_name": 'Hydro Power Plant',
                "Tech_category":  "Wrong category ",
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongTechCategory,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        #multi node
        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Technologies"] = regional_settings["reg2"]["Technologies"].append(
            {
                "Technology": 'Hydro_PP',
                "Tech_name": 'Hydro Power Plant',
                "Tech_category":  "Wrong category ",
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongTechCategory,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )


    def test_regional_settings_wrong_carrier_mapping(self):
        #single node
        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Carrier_input"] = regional_settings["reg1"]["Carrier_input"].append(
            {
                "Technology": "Wrong tech",
                "Carrier_in": "Raw_Oil"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingData,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Carrier_output"] = regional_settings["reg1"]["Carrier_output"].append(
            {
                "Technology": "Oil_refine",
                "Carrier_out": "wrong carrier in"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingData,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        #multi node
        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Carrier_input"] = regional_settings["reg2"]["Carrier_input"].append(
            {
                "Technology": "Wrong tech",
                "Carrier_in": "Raw_Oil"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingData,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )

        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Carrier_output"] = regional_settings["reg2"]["Carrier_output"].append(
            {
                "Technology": "Oil_refine",
                "Carrier_out": "wrong carrier in"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingData,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )


    def test_regional_settings_wrong_carrier_category_mapping(self):
        #single node
        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Carrier_input"] = regional_settings["reg1"]["Carrier_input"].append(
            {
                "Technology": "Oil_extr",
                "Carrier_in": "Raw_Oil"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingTech,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        regional_settings = copy.deepcopy(self.single_node.regional_settings)
        regional_settings["reg1"]["Carrier_output"] = regional_settings["reg1"]["Carrier_output"].append(
            {
                "Technology": "HH_elec_demand",
                "Carrier_out": "Elec_final"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingTech,
            lambda: ModelSettings(
                ModelMode.Planning,
                self.single_node.global_settings,
                regional_settings,
            )
        )

        #multi node
        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Carrier_input"] = regional_settings["reg2"]["Carrier_input"].append(
            {
                "Technology": "Geo_PP",
                "Carrier_in": "Elec"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingTech,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )

        regional_settings = copy.deepcopy(self.multi_node.regional_settings)
        regional_settings["reg2"]["Carrier_output"] = regional_settings["reg2"]["Carrier_output"].append(
            {
                "Technology": "Elec_demand",
                "Carrier_out": "Elec_final"
            },
            ignore_index=True
        )
        self.assertRaises(
            hypatiaException.WrongMappingTech,
            lambda: ModelSettings(
                ModelMode.Operation,
                self.multi_node.global_settings,
                regional_settings,
            )
        )

    """
    Cached properies tests

    Test the ModelSettings cached properies
    """
    def test_regions(self):
        #single node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(
            model_settings.regions,
            ["reg1"]
        )

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(
            model_settings.regions,
            ["reg1", "reg2"]
        )

    def test_technologies(self):
        #single node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(
            model_settings.technologies,
            {
                "reg1": {
                    "Supply": [
                        "Oil_extr",
                        "Hydro_PP",
                    ],
                    "Conversion": [
                        "Oil_refine",
                        "Oil_PP",
                    ],
                    "Transmission": [
                        "Elec_transmission",
                        "Diesel_pipeline",
                    ],
                    "Demand": [
                        "EV",
                        "ICEV",
                        "HH_elec_demand",
                        "Other_elec_demand"
                    ]
                }
            }
        )

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(
            model_settings.technologies,
            {
                "reg1": {
                    "Supply": [
                        "NG_extraction",
                        "Wind_PP",
                        "Hydro_PP"
                    ],
                    "Conversion_plus": [
                        "CHP_PP"
                    ],
                    "Conversion": [
                        "Boiler",
                    ],
                    "Transmission": [
                        "Elec_transmission",
                        "Gas_pipeline",
                    ],
                    "Demand": [
                        "Elec_demand",
                        "Heat_demand",
                    ]
                },
                "reg2": {
                    "Supply": [
                        "Geo_PP",
                        "Solar_PP",
                    ],
                    "Transmission": [
                        "Elec_transmission",
                    ],
                    "Demand": [
                        "Elec_demand",
                    ]
                },

            }
        )

    def test_years(self):
        #single node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(
            model_settings.years,
            ["Y0", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9", "Y10"]
        )

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(
            model_settings.years,
            ["Y0"]
        )

    def test_time_steps(self):
        #single node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(
            model_settings.time_steps,
            ['WD_days', 'WD_nights', 'WE_days', 'WE_nights']
        )

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(
            model_settings.time_steps,
            [str(i) for i in range(1, 8761)]
        )

        #timesteps not define
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings.pop('Timesteps', None)
        model_settings = ModelSettings(
            ModelMode.Operation,
            global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(
            model_settings.time_steps,
            ['Annual']
        )

    def test_timeslice_fraction(self):
        #single node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        expected = np.array(['0.357534246575342', '0.357534246575342',  '0.142465753424658', '0.142465753424658'])
        self.assertTrue(np.array_equal(expected, model_settings.timeslice_fraction))

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        expected = np.array([str(0.000114155251141553) for i in range(1, 8761)])
        self.assertTrue(np.array_equal(expected, model_settings.timeslice_fraction))

        #timesteps not define
        global_settings = copy.deepcopy(self.multi_node.global_settings)
        global_settings.pop('Timesteps', None)
        model_settings = ModelSettings(
            ModelMode.Operation,
            global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(
            model_settings.timeslice_fraction,
            1
        )

    def test_multi_node(self):
        #sigle_node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertFalse(model_settings.multi_node)

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        self.assertTrue(model_settings.multi_node)

    def test_lines_list(self):
        #sigle_node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(model_settings.lines_list, None)

        #multi node
        model_settings = ModelSettings(
            ModelMode.Operation,
            self.multi_node.global_settings,
            self.multi_node.regional_settings,
        )
        self.assertEqual(model_settings.lines_list, ['reg1-reg2'])

    def test_global_parameters_template(self):
        #sigle_node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(model_settings.global_parameters_template, None)

        # TODO(afa) add test for multi region


    def test_trade_parameters_template(self):
        #sigle_node
        model_settings = ModelSettings(
            ModelMode.Planning,
            self.single_node.global_settings,
            self.single_node.regional_settings,
        )
        self.assertEqual(model_settings.trade_parameters_template, None)

        # TODO(afa) add test for multi region

    # TODO(afa) complete test_regional_parameters_template
    # def test_regional_parameters_template(self):
    #     #sigle_node
    #     model_settings = ModelSettings(
    #         ModelMode.Planning,
    #         self.single_node.global_settings,
    #         self.single_node.regional_settings,
    #     )



if __name__ == '__main__':
    unittest.main()
