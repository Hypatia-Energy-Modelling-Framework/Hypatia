import pandas as pd
import numpy as np
import unittest
import copy
from hypatia.backend.ModelSettings import ModelSettings
from hypatia.backend.ModelData import ModelData
from hypatia.utility.constants import ModelMode
from hypatia.examples.ExampleSettings import (
    Utopia2PlanningSingleNodeDN,
    Utopia2OperationMultiNode
)
import hypatia.error_log.Exceptions as hypatiaException

'''
Unit tests for the functions in ModelData.py
'''

class TestModelData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestModelData, self).__init__(*args, **kwargs)
        single_node_settings = Utopia2PlanningSingleNodeDN()
        self.single_node = ModelSettings(
            ModelMode.Planning,
            single_node_settings.global_settings,
            single_node_settings.regional_settings,
        )

        multi_node_settings = Utopia2OperationMultiNode()
        self.multi_node = ModelSettings(
            ModelMode.Operation,
            multi_node_settings.global_settings,
            multi_node_settings.regional_settings,
        )

    """
    Init tests

    Test the ModelData initialization logic
    """
    def test_default(self):
        # single node
        ModelData(
            self.single_node,
            self.single_node.default_global_parameters,
            self.single_node.default_trade_parameters,
            self.single_node.default_regional_parameters
        )

        # multi node
        ModelData(
            self.multi_node,
            self.multi_node.default_global_parameters,
            self.multi_node.default_trade_parameters,
            self.multi_node.default_regional_parameters
        )

    def test_modified_parameters(self):
        # single node
        regional_parameters = self.single_node.default_regional_parameters
        res_capacity_factor = regional_parameters["reg1"]["res_capacity_factor"]
        res_capacity_factor.loc[:, ("Supply", "Oil_extr")] = res_capacity_factor.loc[:, ("Supply", "Oil_extr")].apply(lambda x: x*0.5)
        ModelData(
            self.single_node,
            self.single_node.default_global_parameters,
            self.single_node.default_trade_parameters,
            regional_parameters
        )

        # multi node
        global_parameters = self.multi_node.default_global_parameters
        global_max_production = global_parameters['global_max_production']
        global_max_production.loc["Y0", "NG_extraction"] = 1000
        ModelData(
            self.multi_node,
            global_parameters,
            self.multi_node.default_trade_parameters,
            self.multi_node.default_regional_parameters
        )

    def test_missing_region_parameters(self):
        regional_parameters = self.single_node.default_regional_parameters
        regional_parameters.pop("reg1", None)
        self.assertRaises(
            AssertionError,
            lambda: ModelData(
                self.single_node,
                self.single_node.default_global_parameters,
                self.single_node.default_trade_parameters,
                regional_parameters
            )
        )

        # multi node
        regional_parameters = self.multi_node.default_regional_parameters
        regional_parameters.pop("reg2", None)
        self.assertRaises(
            AssertionError,
            lambda: ModelData(
                self.multi_node,
                self.multi_node.default_global_parameters,
                self.multi_node.default_trade_parameters,
                regional_parameters
            )
        )

    def test_missing_parameter_table(self):
        regional_parameters = self.single_node.default_regional_parameters
        regional_parameters["reg1"].pop("demand", None)
        self.assertRaises(
            AssertionError,
            lambda: ModelData(
                self.single_node,
                self.single_node.default_global_parameters,
                self.single_node.default_trade_parameters,
                regional_parameters
            )
        )

        # multi node
        global_parameters = self.multi_node.default_global_parameters
        global_parameters.pop("global_max_production", None)
        self.assertRaises(
            AssertionError,
            lambda: ModelData(
                self.multi_node,
                global_parameters,
                self.multi_node.default_trade_parameters,
                self.multi_node.default_regional_parameters
            )
        )

    def test_missing_parameter_table(self):
        regional_parameters = self.single_node.default_regional_parameters
        regional_parameters["reg1"].pop("demand", None)
        self.assertRaises(
            AssertionError,
            lambda: ModelData(
                self.single_node,
                self.single_node.default_global_parameters,
                self.single_node.default_trade_parameters,
                regional_parameters
            )
        )

        # multi node
        global_parameters = self.multi_node.default_global_parameters
        global_parameters.pop("global_max_production", None)
        self.assertRaises(
            AssertionError,
            lambda: ModelData(
                self.multi_node,
                global_parameters,
                self.multi_node.default_trade_parameters,
                self.multi_node.default_regional_parameters
            )
        )

    def test_parameters_table_with_nan(self):
        # single node
        regional_parameters = self.single_node.default_regional_parameters
        res_capacity_factor = regional_parameters["reg1"]["res_capacity_factor"]
        res_capacity_factor.loc[("Y0", 1), ("Supply", "Oil_extr")] = np.nan
        self.assertRaises(
            hypatiaException.NanValues,
            lambda: ModelData(
                self.single_node,
                self.single_node.default_global_parameters,
                self.single_node.default_trade_parameters,
                regional_parameters
            )
        )

        # multi node
        global_parameters = self.multi_node.default_global_parameters
        global_max_production = global_parameters['global_max_production']
        global_max_production.loc["Y0", "NG_extraction"] = np.nan
        self.assertRaises(
            hypatiaException.NanValues,
            lambda: ModelData(
                self.multi_node,
                global_parameters,
                self.multi_node.default_trade_parameters,
                self.multi_node.default_regional_parameters
            )
        )



    def test_parameters_table_wrong_columns(self):
        # single node
        regional_parameters = self.single_node.default_regional_parameters
        res_capacity_factor = regional_parameters["reg1"]["res_capacity_factor"]
        res_capacity_factor.columns = pd.MultiIndex.from_product([
            ["Wrong category 1", "Wrong category 2"],
            ["Wrong tech 1", "Wrong tech 2", "Wrong tech 3"],
        ])
        self.assertRaises(
            hypatiaException.WrongIndex,
            lambda: ModelData(
                self.single_node,
                self.single_node.default_global_parameters,
                self.single_node.default_trade_parameters,
                regional_parameters
            )
        )

        # multi node
        global_parameters = self.multi_node.default_global_parameters
        global_max_production = global_parameters['global_max_production']
        global_max_production.index = pd.Index(["Wrong year"], name="Years")
        self.assertRaises(
            hypatiaException.WrongIndex,
            lambda: ModelData(
                self.multi_node,
                global_parameters,
                self.multi_node.default_trade_parameters,
                self.multi_node.default_regional_parameters
            )
        )
