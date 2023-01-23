from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from hypatia.utility.utility import _calc_variable_overall
import pandas as pd

"""
Defines the upper and lower limit on the aggregated new installed capacity
of each technology over all the regions
"""
class NewCapacityGlobal(Constraint):
    MODES = [ModelMode.Planning]
    TOPOLOGY_TYPES = [TopologyType.MultiNode]

    def _check(self):
        assert self.variables.real_new_capacity != None, "new_capacity cannot be None"

    def rules(self):
        newcapacity_overall = _calc_variable_overall(
            self.model_data.settings.global_settings["Technologies_glob"],
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.technologies,
            self.variables.real_new_capacity,
        )

        rules = []
        for tech, value in newcapacity_overall.items():
            rules.append(
                value - self.model_data.global_parameters["global_min_newcap"].loc[:, tech] >= 0
            )
            rules.append(
                value - self.model_data.global_parameters["global_max_newcap"].loc[:, tech] <= 0
            )

        return rules

    def _required_global_parameters(settings):
        return {
            "global_min_newcap": {
                "sheet_name": "Min_newcap_global",
                "value": 0,
                "index": pd.Index(settings.years, name="Years"),
                "columns": pd.Index(
                    settings.global_settings["Technologies_glob"].loc[
                        settings.global_settings["Technologies_glob"]["Tech_category"]
                        != "Demand"
                    ]["Technology"],
                )
            },
            "global_max_newcap": {
                "sheet_name": "Max_newcap_global",
                "value": 1e10,
                "index": pd.Index(settings.years, name="Years"),
                "columns": pd.Index(
                    settings.global_settings["Technologies_glob"].loc[
                        settings.global_settings["Technologies_glob"]["Tech_category"]
                        != "Demand"
                    ]["Technology"],
                )
            },
        }
