import pandas as pd
import itertools as it
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
from hypatia.utility.utility import create_technology_columns
from hypatia.backend.constraints.ConstraintList import CONSTRAINTS

class ModelSettings:
    """
    A class that represents the Hypatia model settings data, which includes the information that
    has historically been stored in the sets folder.

    Attributes
    ------------
    mode:
        The mode of optimization including the operation and planning mode

    global_settings : dict
        A dictionary of the global set tables given by the user in the global.xlsx file

    regional_settings : dict
        A dictionary of the regional set tables given by the user in the regional
        set files
    """

    def __init__(
        self,
        mode: ModelMode,
        global_settings: Dict[str, pd.DataFrame],
        regional_settings: Dict[str, Dict[str, pd.DataFrame]],
    ):
        self.mode = mode
        self.global_settings = global_settings
        self.regional_settings = regional_settings
        self._validate_global_settings()
        self._validate_regional_settings()

    def _validate_global_settings(self):
        for table_name, table in self.global_settings.items():
            check_table_name(
                file_name="global",
                allowed_names=list(global_set_ids.keys()),
                table_name=table_name,
            )

            check_index(table.columns, table_name, "global", pd.Index(global_set_ids[table_name]))

            check_nan(table_name, table, "global")

            if table_name == "Technologies_glob":
                check_tech_category(table, technology_categories, "global")

            if table_name == "Carriers_glob":
                check_carrier_type(table, carrier_types, "global")

    def _validate_regional_settings(self):
        for reg in self.regions:
            for table_name, table in self.regional_settings[reg].items():
                check_table_name(
                    file_name=reg,
                    allowed_names=list(regional_set_ids.keys()),
                    table_name=table_name,
                )

                check_index(table.columns, table_name, reg, pd.Index(regional_set_ids[table_name]))

                check_nan(table_name, table, reg)

                if table_name == "Technologies":
                    check_tech_category(table, technology_categories, reg)

                if table_name == "Carriers":
                    check_carrier_type(table, carrier_types, reg)

                if table_name == "Carrier_input" or table_name == "Carrier_output":
                    check_mapping_values(
                        table,
                        table_name,
                        self.regional_settings[reg]["Technologies"],
                        "Technologies",
                        "Technology",
                        "Technology",
                        reg,
                    )

            check_mapping_values(
                self.regional_settings[reg]["Carrier_input"],
                "Carrier_input",
                self.regional_settings[reg]["Carriers"],
                "Carriers",
                "Carrier_in",
                "Carrier",
                reg,
            )

            check_mapping_values(
                self.regional_settings[reg]["Carrier_output"],
                "Carrier_output",
                self.regional_settings[reg]["Carriers"],
                "Carriers",
                "Carrier_out",
                "Carrier",
                reg,
            )

            check_mapping_ctgry(
                self.regional_settings[reg]["Carrier_input"],
                "Carrier_input",
                self.regional_settings[reg]["Technologies"],
                "Supply",
                reg,
            )

            check_mapping_ctgry(
                self.regional_settings[reg]["Carrier_output"],
                "Carrier_output",
                self.regional_settings[reg]["Technologies"],
                "Demand",
                reg,
            )

    @cached_property
    def regions(self) -> List[str]:
        return list(self.global_settings["Regions"]["Region"])

    @cached_property
    def technologies(self):
        technologies = {}
        for reg in self.regions:
            regional_tech = {}
            for key in list(self.regional_settings[reg]["Technologies"]["Tech_category"]):
                regional_tech[key] = list(
                    self.regional_settings[reg]["Technologies"].loc[
                        self.regional_settings[reg]["Technologies"]["Tech_category"] == key
                    ]["Technology"]
                )
            technologies[reg] = regional_tech
        return technologies

    @cached_property
    def years(self) -> List[str]:
        return list(self.global_settings["Years"]["Year"])

    @cached_property
    def time_steps(self) -> List[str]:
        if "Timesteps" in self.global_settings.keys():
            return  list(self.global_settings["Timesteps"]["Timeslice"])
        else:
            return ["Annual"]

    @cached_property
    def timeslice_fraction(self):
        if "Timesteps" in self.global_settings.keys():
            return self.global_settings["Timesteps"][
                "Timeslice_fraction"
            ].values
        else:
            return 1

    @cached_property
    def multi_node(self):
        if len(self.regions) > 1:
            return True
        return False

    @cached_property
    def lines_list(self) -> Optional[List[str]]:
        if not self.multi_node:
            return None

        lines_list = []
        for item in it.permutations(self.regions, r=2):
            if item[0] < item[1]:
                lines_list.append("{}-{}".format(item[0], item[1]))
        return lines_list

    @cached_property
    def default_global_parameters(self) -> Optional[Dict]:
        if self.global_parameters_template == None:
            return None

        default_paramenters = {}
        for key, value in self.global_parameters_template.items():
            default_paramenters[key] = pd.DataFrame(
                value["value"], index=value["index"], columns=value["columns"]
            )
        return default_paramenters

    @cached_property
    def default_trade_parameters(self) -> Optional[Dict]:
        if self.trade_parameters_template == None:
            return None

        default_paramenters = {}
        for key, value in self.trade_parameters_template.items():
            default_paramenters[key] = pd.DataFrame(
                value["value"], index=value["index"], columns=value["columns"]
            )
        return default_paramenters

    @cached_property
    def default_regional_parameters(self) -> Dict:
        default_paramenters = {}
        for region in self.regions:
            default_regional_paramenters = {}
            for key, value in self.regional_parameters_template[region].items():
                default_regional_paramenters[key] = pd.DataFrame(
                    value["value"], index=value["index"], columns=value["columns"]
                )
            default_paramenters[region] = default_regional_paramenters
        return default_paramenters

    @cached_property
    def global_parameters_template(self) -> Optional[Dict]:
        if not self.multi_node:
            return None

        global_parameters_template = {}
        if self.mode == ModelMode.Planning:
            global_parameters_template.update(
                {
                    "global_discount_rate": {
                        "sheet_name": "Discount_rate",
                        "value": 0.05,
                        "index": pd.Index(self.years, name="Years"),
                        "columns": pd.Index(["Annual Discount Rate"]),
                    },
                }
            )

        # collect global parameters from constraints
        for costr in CONSTRAINTS:
            global_parameters_template.update(
                costr.required_global_parameters(costr, self)
            )

        return global_parameters_template

    @cached_property
    def trade_parameters_template(self) -> Optional[Dict]:
        if not self.multi_node:
            return None

        indexer = pd.MultiIndex.from_product(
            [self.lines_list, self.global_settings["Carriers_glob"]["Carrier"]],
            names=["Line", "Transmitted Carrier"],
        )

        connection_parameters_template = {
            "line_fixed_cost": {
                "sheet_name": "F_OM",
                "value": 0,
                "index": pd.Index(self.years, name="Years"),
                "columns": indexer,
            },
            "line_var_cost": {
                "sheet_name": "V_OM",
                "value": 0,
                "index": pd.Index(self.years, name="Years"),
                "columns": indexer,
            },
            "line_residual_cap": {
                "sheet_name": "Residual_capacity",
                "value": 0,
                "index": pd.Index(self.years, name="Years"),
                "columns": indexer,
            },
            "line_eff": {
                "sheet_name": "Line_efficiency",
                "value": 1,
                "index": pd.Index(self.years, name="Years"),
                "columns": indexer,
            },
        }

        if self.mode == ModelMode.Planning:
            connection_parameters_template.update(
                {
                    "line_inv": {
                        "sheet_name": "INV",
                        "value": 0,
                        "index": pd.Index(self.years, name="Years"),
                        "columns": indexer,
                    },
                    "line_decom_cost": {
                        "sheet_name": "Decom_cost",
                        "value": 0,
                        "index": pd.Index(self.years, name="Years"),
                        "columns": indexer,
                    },
                    "line_lifetime": {
                        "sheet_name": "Line_lifetime",
                        "value": 1,
                        "index": pd.Index(
                            ["Technical Life Time"], name="Performance Parameter"
                        ),
                        "columns": indexer,
                    },
                    "line_economic_lifetime": {
                        "sheet_name": "Line_Economic_life",
                        "value": 1,
                        "index": pd.Index(
                            ["Economic Life time"], name="Performance Parameter"
                        ),
                        "columns": indexer,
                    },
                    "interest_rate": {
                        "sheet_name": "Interest_rate",
                        "value": 0.05,
                        "index": pd.Index(
                            ["Interest Rate"], name="Performance Parameter"
                        ),
                        "columns": indexer,
                    },
                }
            )

        # collect trade parameters from constraints
        for costr in CONSTRAINTS:
            connection_parameters_template.update(
                costr.required_trade_parameters(costr, self)
            )

        return connection_parameters_template

    @cached_property
    def regional_parameters_template(self) -> Optional[Dict]:
        regional_parameters_template = {}
        for reg in self.regions:
            # Creates the columns of the technology-specific parameter files
            # based on the technology categories and the technologies within each
            # caregory
            indexer_reg = create_technology_columns(
                self.technologies[reg],
                ignored_tech_categories=["Demand"],
            )

            indexer_reg_drop1 = create_technology_columns(
                self.technologies[reg],
                ignored_tech_categories=["Demand", "Storage"],
            )

            indexer_reg_drop2 = create_technology_columns(
                self.technologies[reg],
                ignored_tech_categories=["Demand", "Storage", "Transmission"],
            )

            add_indexer = create_technology_columns(
                self.technologies[reg],
                ignored_tech_categories=["Demand"],
                additional_level=("Taxes or Subsidies", ["Tax", "Sub"])
            )

            regional_parameters_template[reg] = {
                "tech_fixed_cost": {
                    "sheet_name": "F_OM",
                    "value": 0,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": indexer_reg,
                },
                "tech_var_cost": {
                    "sheet_name": "V_OM",
                    "value": 0,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": indexer_reg,
                },
                "tech_residual_cap": {
                    "sheet_name": "Residual_capacity",
                    "value": 0,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": indexer_reg,
                },
                "tech_capacity_factor": {
                    "sheet_name": "Capacity_factor_tech",
                    "value": 1,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": indexer_reg,
                },
                "specific_emission": {
                    "sheet_name": "Specific_emission",
                    "value": 0,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": indexer_reg_drop2,
                },
                "carbon_tax": {
                    "sheet_name": "Carbon_tax",
                    "value": 0,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": indexer_reg_drop2,
                },
                "fix_taxsub": {
                    "sheet_name": "Fix_taxsub",
                    "value": 0,
                    "index": pd.Index(self.years, name="Years"),
                    "columns": add_indexer,
                },
                "annualprod_per_unitcapacity": {
                    "sheet_name": "AnnualProd_perunit_capacity",
                    "value": 1,
                    "index": pd.Index(
                        ["AnnualProd_Per_UnitCapacity"], name="Performance Parameter"
                    ),
                    "columns": indexer_reg,
                },
            }

            if self.mode == ModelMode.Planning:
                regional_parameters_template[reg].update(
                    {
                        "tech_inv": {
                            "sheet_name": "INV",
                            "value": 0,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": indexer_reg,
                        },
                        "inv_taxsub": {
                            "sheet_name": "Investment_taxsub",
                            "value": 0,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": add_indexer,
                        },
                        "tech_decom_cost": {
                            "sheet_name": "Decom_cost",
                            "value": 0,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": indexer_reg,
                        },
                        "discount_rate": {
                            "sheet_name": "Discount_rate",
                            "value": 0.05,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": pd.Index(["Annual Discount Rate"]),
                        },
                        "tech_lifetime": {
                            "sheet_name": "Tech_lifetime",
                            "value": 1,
                            "index": pd.Index(
                                ["Technical Life time"], name="Performance Parameter"
                            ),
                            "columns": indexer_reg,
                        },
                        "economic_lifetime": {
                            "sheet_name": "Economic_lifetime",
                            "value": 1,
                            "index": pd.Index(
                                ["Economic Life time"], name="Performance Parameter"
                            ),
                            "columns": indexer_reg,
                        },
                        "interest_rate": {
                            "sheet_name": "Interest_rate",
                            "value": 0.05,
                            "index": pd.Index(
                                ["Interest Rate"], name="Performance Parameter"
                            ),
                            "columns": indexer_reg,
                        },
                    }
                )

            if "Storage" in self.technologies[reg].keys():
                regional_parameters_template[reg].update(
                    {
                        "storage_charge_efficiency": {
                            "sheet_name": "Storage_charge_efficiency",
                            "value": 1,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": pd.Index(
                                self.technologies[reg]["Storage"], name="Technology"
                            ),
                        },
                        "storage_discharge_efficiency": {
                            "sheet_name": "Storage_discharge_efficiency",
                            "value": 1,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": pd.Index(
                                self.technologies[reg]["Storage"], name="Technology"
                            ),
                        },
                        "storage_min_SOC": {
                            "sheet_name": "Storage_min_SOC",
                            "value": 0,
                            "index": pd.Index(self.years, name="Years"),
                            "columns": pd.Index(
                                self.technologies[reg]["Storage"], name="Technology"
                            ),
                        },
                        "storage_initial_SOC": {
                            "sheet_name": "Storage_initial_SOC",
                            "value": 0,
                            "index": ["Initial State of Charge"],
                            "columns": pd.Index(
                                self.technologies[reg]["Storage"], name="Technology"
                            ),
                        },
                        "storage_charge_time": {
                            "sheet_name": "Storage_charge_time",
                            "value": 1,
                            "index": ["Charging Time of Storage in Hours"],
                            "columns": pd.Index(
                                self.technologies[reg]["Storage"], name="Technology"
                            ),
                        },
                        "storage_discharge_time": {
                            "sheet_name": "Storage_discharge_time",
                            "value": 1,
                            "index": ["Discharging Time of Storage in Hours"],
                            "columns": pd.Index(
                                self.technologies[reg]["Storage"], name="Technology"
                            ),
                        },
                    }
                )

            if "Timesteps" in self.global_settings.keys():
                indexer_time = pd.MultiIndex.from_product(
                    [self.years, self.time_steps],
                    names=["Years", "Timesteps"],
                )
            else:
                indexer_time = pd.MultiIndex.from_arrays(
                    [self.years, self.years],
                    names=["Years", "Timesteps"],
                )

            regional_parameters_template[reg].update(
                {
                    "demand": {
                        "sheet_name": "Demand",
                        "value": 0,
                        "index": indexer_time,
                        "columns": pd.Index(self.technologies[reg]["Demand"]),
                    },
                    "res_capacity_factor": {
                        "sheet_name": "capacity_factor_resource",
                        "value": 1,
                        "index": indexer_time,
                        "columns": indexer_reg_drop1,
                    },
                }
            )
            if "Conversion_plus" in self.technologies[reg].keys():
                take_carrierin = [
                    self.regional_settings[reg]["Carrier_input"]
                    .loc[self.regional_settings[reg]["Carrier_input"]["Technology"] == tech][
                        "Carrier_in"
                    ]
                    .values
                    for tech in self.technologies[reg]["Conversion_plus"]
                ]

                take_carrierin_ = [
                    carr
                    for index, value in enumerate(take_carrierin)
                    for carr in take_carrierin[index]
                ]

                take_technologyin = [
                    self.regional_settings[reg]["Carrier_input"]
                    .loc[self.regional_settings[reg]["Carrier_input"]["Technology"] == tech][
                        "Technology"
                    ]
                    .values
                    for tech in self.technologies[reg]["Conversion_plus"]
                ]

                take_technologyin_ = [
                    tech
                    for index, value in enumerate(take_technologyin)
                    for tech in take_technologyin[index]
                ]

                take_carrierout = [
                    self.regional_settings[reg]["Carrier_output"]
                    .loc[self.regional_settings[reg]["Carrier_output"]["Technology"] == tech][
                        "Carrier_out"
                    ]
                    .values
                    for tech in self.technologies[reg]["Conversion_plus"]
                ]

                take_carrierout_ = [
                    carr
                    for index, value in enumerate(take_carrierout)
                    for carr in take_carrierout[index]
                ]

                take_technologyout = [
                    self.regional_settings[reg]["Carrier_output"]
                    .loc[self.regional_settings[reg]["Carrier_output"]["Technology"] == tech][
                        "Technology"
                    ]
                    .values
                    for tech in self.technologies[reg]["Conversion_plus"]
                ]

                take_technologyout_ = [
                    tech
                    for index, value in enumerate(take_technologyout)
                    for tech in take_technologyout[index]
                ]

                regional_parameters_template[reg].update(
                    {
                        "carrier_ratio_in": {
                            "sheet_name": "Carrier_ratio_in",
                            "value": 1,
                            "index": indexer_time,
                            "columns": pd.MultiIndex.from_arrays(
                                [take_technologyin_, take_carrierin_],
                                names=["Tech_category", "Technology"],
                            ),
                        },
                        "carrier_ratio_out": {
                            "sheet_name": "Carrier_ratio_out",
                            "value": 1,
                            "index": indexer_time,
                            "columns": pd.MultiIndex.from_arrays(
                                [take_technologyout_, take_carrierout_],
                                names=["Tech_category", "Technology"],
                            ),
                        },
                    }
                )

        # collect regional parameters from constraints
        for costr in CONSTRAINTS:
            for region, parameters in costr.required_regional_parameters(costr, self).items():
                regional_parameters_template[region].update(parameters)

        return regional_parameters_template
