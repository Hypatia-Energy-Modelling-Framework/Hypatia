import pandas as pd
from functools import cached_property
from typing import (
    Dict,
    List,
    Optional
)
from hypatia.utility.constants import (
    global_set_ids,
    regional_set_ids,
    ModelMode,
    technology_categories,
    carrier_types,
)
from hypatia.error_log.Checks import (
    check_nan,
    check_index,
    check_index_data,
    check_table_name,
    check_mapping_values,
    check_mapping_ctgry,
    check_sheet_name,
    check_tech_category,
    check_carrier_type,
    check_years_mode_consistency,
)
from hypatia.backend.ModelSettings import ModelSettings

"""
A class that represents the Hypatia model data.
This includes both the settings and the parameters data

Attributes
------------
model_settings: ModelSettingData
global_parameters : dict
    A nested dictionary for storing the global parameters

regional_parameters : dict
    A nested dictionary for storing the regional parameters

trade_parameters : dict
    A nested dictionary for storing the inter-regional link data
"""
class ModelData:
    def __init__(
        self,
        settings: ModelSettings,
        global_parameters: Optional[Dict[str, pd.DataFrame]],
        trade_parameters: Optional[Dict[str, pd.DataFrame]],
        regional_parameters: Dict[str, Dict[str, pd.DataFrame]],
    ):
        self.settings = settings
        self.global_parameters = global_parameters
        self.trade_parameters = trade_parameters
        self.regional_parameters = regional_parameters
        self._validate_global_parameters()
        self._validate_trade_parameters()
        self._validate_regional_parameters()

    def _validate_global_parameters(self):
        global_parameters_templete = self.settings.global_parameters_template
        if global_parameters_templete == None:
            assert self.global_parameters == None, "Global parameters should be None"
            return

        for key, value in global_parameters_templete.items():
            assert key in self.global_parameters.keys(), r"{} should be presents in global parameters.".format(key)
            check_nan(value["sheet_name"], self.global_parameters[key], "parameters_global")
            print(self.global_parameters[key].index)
            check_index_data(
                self.global_parameters[key].index,
                value["sheet_name"],
                "parameters_global",
                pd.Index(value["index"]),
            )
            check_index_data(
                self.global_parameters[key].columns,
                value["sheet_name"],
                "parameters_global",
                pd.Index(value["columns"]),
            )

    def _validate_trade_parameters(self):
        trade_parameters_templete = self.settings.trade_parameters_template
        if trade_parameters_templete == None:
            assert self.trade_parameters == None, "Trade parameters should be None"
            return

        for key, value in trade_parameters_templete.items():
            assert key in self.trade_parameters.keys(), r"{} should be presents in trade parameters.".format(key)
            check_nan(value["sheet_name"], self.trade_parameters[key], "parameters_connections")
            check_index_data(
                self.trade_parameters[key].index,
                value["sheet_name"],
                "parameters_connections",
                pd.Index(value["index"]),
            )
            check_index_data(
                self.trade_parameters[key].columns,
                value["sheet_name"],
                "parameters_connections",
                pd.Index(value["columns"]),
            )

    def _validate_regional_parameters(self):
        for region in self.settings.regions:
            assert region in self.regional_parameters.keys(), r"Parameters for {} are missing from regional parameters.".format(region)
            for key, value in self.settings.regional_parameters_template[region].items():
                assert key in self.regional_parameters[region].keys(), r'{} should be presents in regional parameters for {}.'.format(key, region)
                check_nan(value["sheet_name"], self.regional_parameters[region][key], "parameters_global")
                check_index_data(
                    self.regional_parameters[region][key].index,
                    value["sheet_name"],
                    "parameters_{region}",
                    pd.Index(value["index"]),
                )
                check_index_data(
                    self.regional_parameters[region][key].columns,
                    value["sheet_name"],
                    "parameters_{region}",
                    pd.Index(value["columns"]),
                )
