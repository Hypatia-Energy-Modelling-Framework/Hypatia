from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
import pandas as pd

"""
Defines the upper and lower limit on the annual new installed capacity
of the inter-regional links
"""
class LineNewCapacity(Constraint):
    MODES = [ModelMode.Planning]
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert self.variables.line_new_capacity != None, "new_capacity cannot be None"

    def rules(self):
        rules = []
        for key, value in self.variables.line_new_capacity.items():
            rules.append(value <= self.model_data.trade_parameters["line_max_newcap"][key])
            rules.append(value >= self.model_data.trade_parameters["line_min_newcap"][key])
        return rules

    def _required_trade_parameters(settings):
        indexer = pd.MultiIndex.from_product(
            [settings.lines_list, settings.global_settings["Carriers_glob"]["Carrier"]],
            names=["Line", "Transmitted Carrier"],
        )

        return {
            "line_min_newcap": {
                "sheet_name": "Min_newcap",
                "value": 0,
                "index": pd.Index(settings.years, name="Years"),
                "columns": indexer,
            },
            "line_max_newcap": {
                "sheet_name": "Max_newcap",
                "value": 1e10,
                "index": pd.Index(settings.years, name="Years"),
                "columns": indexer,
            },
        }
