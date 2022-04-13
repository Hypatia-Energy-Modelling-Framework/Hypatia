from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
import cvxpy as cp
import numpy as np
import pandas as pd

"""
Guarantees the adequecy of inter-regional link capacities based on their
capacity factor
"""
class LineAvailability(Constraint):
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert self.variables.line_import != None, "line_import cannot be None"
        assert hasattr(self.variables, 'line_totalcapacity'), "line_totalcapacity must be defined"

    def rules(self):
        timeslice_fraction = self.model_data.settings.timeslice_fraction
        if not isinstance(timeslice_fraction, int):
            timeslice_fraction.shape = (len(self.model_data.settings.time_steps), 1)


        rules = []
        for reg in self.model_data.settings.regions:
            for key, value in self.variables.line_import[reg].items():
                for indx, year in enumerate(self.model_data.settings.years):
                    if "{}-{}".format(reg, key) in self.model_data.settings.lines_list:
                        capacity_factor = (
                            self.model_data.trade_parameters["line_capacity_factor"]
                            .loc[year, ("{}-{}".format(reg, key), slice(None))]
                            .values
                        )
                        capacity_to_production = (
                            self.model_data.trade_parameters["annualprod_per_unitcapacity"]
                            .loc[:, ("{}-{}".format(reg, key), slice(None))]
                            .values
                        )
                        capacity = self.variables.line_totalcapacity["{}-{}".format(reg, key)][
                            indx : indx + 1, :
                        ]
                    elif "{}-{}".format(key, reg) in self.model_data.settings.lines_list:
                        capacity_factor = (
                            self.model_data.trade_parameters["line_capacity_factor"]
                            .loc[year, ("{}-{}".format(key, reg), slice(None))]
                            .values
                        )
                        capacity_to_production = (
                            self.model_data.trade_parameters["annualprod_per_unitcapacity"]
                            .loc[:, ("{}-{}".format(key, reg), slice(None))]
                            .values
                        )
                        capacity = self.variables.line_totalcapacity["{}-{}".format(key, reg)][
                            indx : indx + 1, :
                        ]

                    line_import = cp.sum(
                        value[
                            indx
                            * len(self.model_data.settings.time_steps) : (indx + 1)
                            * len(self.model_data.settings.time_steps),
                            :,
                        ],
                        axis=0,
                    )
                    line_import = cp.reshape(line_import, capacity_to_production.shape)
                    capacity_factor.shape = capacity_to_production.shape

                    rules.append(
                        cp.multiply(
                            cp.multiply(capacity, capacity_to_production),
                            timeslice_fraction,
                        )
                        - value[
                            indx
                            * len(self.model_data.settings.time_steps) : (indx + 1)
                            * len(self.model_data.settings.time_steps),
                            :,
                        ]
                        >= 0
                    )
                    rules.append(
                        cp.multiply(
                            cp.multiply(capacity, capacity_factor),
                            capacity_to_production,
                        )
                        - line_import
                        >= 0
                    )

        return rules

    def _required_trade_parameters(settings):
        indexer = pd.MultiIndex.from_product(
            [settings.lines_list, settings.global_settings["Carriers_glob"]["Carrier"]],
            names=["Line", "Transmitted Carrier"],
        )

        return {
            "line_capacity_factor": {
                "sheet_name": "Capacity_factor_line",
                "value": 1,
                "index": pd.Index(settings.years, name="Years"),
                "columns": indexer,
            },
            "annualprod_per_unitcapacity": {
                "sheet_name": "AnnualProd_perunit_capacity",
                "value": 1,
                "index": pd.Index(
                    ["AnnualProd_Per_UnitCapacity"], name="Performance Parameter"
                ),
                "columns": indexer,
            },
        }
