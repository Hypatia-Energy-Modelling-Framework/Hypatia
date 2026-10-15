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
    OptimizationMode,
    EnsureFeasibility,
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
from hypatia.error_log.Exceptions import (
    WrongIndex,
    WrongMappingData,
)
from hypatia.backend.ModelSettings import ModelSettings
from hypatia.utility.utility import CAPACITY_GROUP_SHEETS

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
        self._validate_optional_capacity_group_parameters()

    def _validate_global_parameters(self):
        global_parameters_templete = self.settings.global_parameters_template
        if global_parameters_templete == None:
            assert self.global_parameters == None, "Global parameters should be None"
            return

        for key, value in global_parameters_templete.items():
            assert key in self.global_parameters.keys(), r"{} should be presents in global parameters.".format(key)
            check_nan(value["sheet_name"], self.global_parameters[key], "parameters_global")
            # print(self.global_parameters[key].index)
            # Templates with "variable_index": True have user-defined rows
            # (e.g. one row per CHP group): only their columns are checked.
            if not value.get("variable_index", False):
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
            # Templates with "variable_index": True have user-defined rows
            # (e.g. one row per CHP group): only their columns are checked.
            if not value.get("variable_index", False):
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
                check_nan(value["sheet_name"], self.regional_parameters[region][key], "parameters_regional")
                # Templates with "variable_index": True have user-defined rows
                # (e.g. one row per CHP group): only their columns are checked.
                if not value.get("variable_index", False):
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

    def _validate_optional_capacity_group_parameters(self):
        if self.settings.multi_node:
            self._validate_capacity_group_parameter_block(
                self.global_parameters,
                "parameters_global",
            )
            return

        region = self.settings.regions[0]
        self._validate_capacity_group_parameter_block(
            self.regional_parameters[region],
            "parameters_{}".format(region),
        )

    def _validate_capacity_group_parameter_block(self, parameter_block, file_name):
        if parameter_block is None:
            return

        membership = parameter_block.get("capacity_group_membership")
        group_max_newcap = parameter_block.get("group_max_newcap")
        group_maxtotcap = parameter_block.get("group_maxtotcap")

        optional_tables = [membership, group_max_newcap, group_maxtotcap]
        if all(table is None for table in optional_tables):
            return

        if all(table is None or table.empty for table in optional_tables):
            return

        if membership is None or membership.empty:
            raise WrongIndex(
                "The '{}' sheet must contain at least one group-technology row whenever grouped capacity limits are provided in '{}'.".format(
                    CAPACITY_GROUP_SHEETS["capacity_group_membership"]["sheet_name"],
                    file_name,
                )
            )

        membership_sheet_name = CAPACITY_GROUP_SHEETS["capacity_group_membership"]["sheet_name"]
        check_nan(membership_sheet_name, membership, file_name)
        check_index(
            membership.columns,
            membership_sheet_name,
            file_name,
            pd.Index(CAPACITY_GROUP_SHEETS["capacity_group_membership"]["columns"]),
        )

        duplicate_memberships = membership.duplicated(subset=["Group", "Technology"])
        if duplicate_memberships.any():
            duplicates = membership.loc[
                duplicate_memberships,
                ["Group", "Technology"],
            ].values.tolist()
            raise WrongIndex(
                "Duplicate technology memberships were found in '{}' of '{}': {}".format(
                    membership_sheet_name,
                    file_name,
                    duplicates,
                )
            )

        allowed_technologies = set(
            self.settings.global_settings["Technologies_glob"]
            .loc[
                self.settings.global_settings["Technologies_glob"]["Tech_category"] != "Demand",
                "Technology",
            ]
            .tolist()
        )

        unknown_technologies = sorted(
            set(membership["Technology"].tolist()) - allowed_technologies
        )
        if unknown_technologies:
            raise WrongMappingData(
                "The '{}' sheet in '{}' includes technologies that are not defined among the model technologies: {}".format(
                    membership_sheet_name,
                    file_name,
                    unknown_technologies,
                )
            )

        tech_units = self.settings.global_settings["Technologies_glob"].set_index(
            "Technology"
        )["Tech_cap_unit"]

        group_members = (
            membership.groupby("Group", sort=False)["Technology"]
            .apply(list)
            .to_dict()
        )

        for group_name, techs in group_members.items():
            if len(techs) == 0:
                raise WrongMappingData(
                    "The capacity group '{}' in '{}' does not include any technologies.".format(
                        group_name,
                        membership_sheet_name,
                    )
                )

            group_units = tech_units.loc[techs].dropna().unique().tolist()
            if len(group_units) > 1:
                raise WrongMappingData(
                    "The capacity group '{}' mixes incompatible capacity units {} in '{}'. Grouped capacity limits must sum technologies with the same capacity unit.".format(
                        group_name,
                        group_units,
                        file_name,
                    )
                )

        used_groups = set()
        used_groups.update(
            self._validate_capacity_group_limit_table(
                group_max_newcap,
                "group_max_newcap",
                file_name,
                set(group_members.keys()),
            )
        )
        used_groups.update(
            self._validate_capacity_group_limit_table(
                group_maxtotcap,
                "group_maxtotcap",
                file_name,
                set(group_members.keys()),
            )
        )

        if not used_groups:
            raise WrongMappingData(
                "The '{}' sheet in '{}' defines groups, but no grouped max-new-cap or max-total-cap limits were provided.".format(
                    membership_sheet_name,
                    file_name,
                )
            )

        unused_groups = sorted(set(group_members.keys()) - used_groups)
        if unused_groups:
            raise WrongMappingData(
                "The following capacity groups are defined in '{}' but never used by any grouped capacity limit sheet in '{}': {}".format(
                    membership_sheet_name,
                    file_name,
                    unused_groups,
                )
            )

    def _validate_capacity_group_limit_table(
        self,
        limit_table,
        table_key,
        file_name,
        defined_groups,
    ):
        if limit_table is None:
            return set()

        table_definition = CAPACITY_GROUP_SHEETS[table_key]
        sheet_name = table_definition["sheet_name"]
        value_column = table_definition["columns"][-1]

        check_nan(sheet_name, limit_table, file_name)
        check_index(
            limit_table.columns,
            sheet_name,
            file_name,
            pd.Index(table_definition["columns"]),
        )

        if limit_table.empty:
            return set()

        duplicate_rows = limit_table.duplicated(subset=["Group", "Year"])
        if duplicate_rows.any():
            duplicates = limit_table.loc[
                duplicate_rows,
                ["Group", "Year"],
            ].values.tolist()
            raise WrongIndex(
                "Duplicate group-year entries were found in '{}' of '{}': {}".format(
                    sheet_name,
                    file_name,
                    duplicates,
                )
            )

        unknown_groups = sorted(
            set(limit_table["Group"].tolist()) - defined_groups
        )
        if unknown_groups:
            raise WrongMappingData(
                "The '{}' sheet in '{}' includes limits for undefined capacity groups: {}".format(
                    sheet_name,
                    file_name,
                    unknown_groups,
                )
            )

        model_years = set(self.settings.years)
        unknown_years = sorted(set(limit_table["Year"].tolist()) - model_years)
        if unknown_years:
            raise WrongIndex(
                "The '{}' sheet in '{}' includes years outside the model horizon: {}".format(
                    sheet_name,
                    file_name,
                    unknown_years,
                )
            )

        numeric_values = pd.to_numeric(limit_table[value_column], errors="coerce")
        if numeric_values.isna().any():
            raise WrongIndex(
                "The '{}' column in '{}' of '{}' must contain numeric values only.".format(
                    value_column,
                    sheet_name,
                    file_name,
                )
            )

        limit_table.loc[:, value_column] = numeric_values.values

        groups_in_table = set(limit_table["Group"].tolist())
        for group_name in groups_in_table:
            group_years = set(
                limit_table.loc[limit_table["Group"] == group_name, "Year"].tolist()
            )
            if group_years != model_years:
                missing_years = sorted(model_years - group_years)
                raise WrongIndex(
                    "The '{}' sheet in '{}' is missing model years {} for capacity group '{}'.".format(
                        sheet_name,
                        file_name,
                        missing_years,
                        group_name,
                    )
                )

        return groups_in_table
