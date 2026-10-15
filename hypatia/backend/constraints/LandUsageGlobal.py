from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
import pandas as pd
from hypatia.backend.constraints._terms import sum_terms

"""
Defines the upper limit on the annual land usage
of each technology globally
"""
class LandUsageGlobal(Constraint):
    MODES = [ModelMode.Planning]
    TOPOLOGY_TYPES = [TopologyType.MultiNode]
    _sum_terms = staticmethod(sum_terms)

    def _check(self):
        assert hasattr(self.variables, 'totalcapacity'), "totalcapacity must be defined"
        assert hasattr(self.variables, 'land_usage'), "land_usage must be defined"

    def rules(self):
        rules = []
        for tech in list(
            self.model_data.settings.global_settings["Technologies_glob"].loc[
                (self.model_data.settings.global_settings["Technologies_glob"]["Tech_category"] != "Demand")
            ]["Technology"]
        ):
            landusage_terms = []
            for reg in self.model_data.settings.regions:
                for key, value in self.model_data.settings.technologies[reg].items():

                    if tech in value:

                        landusage_terms.append(
                            self.variables.land_usage[reg][key][:, value.index(tech)]
                        )

            landusage_overall = self._sum_terms(landusage_terms)
            if landusage_overall is not None:
                rules.append(
                    landusage_overall -
                    self.model_data.global_parameters["global_max_land_usage"].loc[:, tech] <= 0)
                        
        return rules
    
    def _required_global_parameters(settings):
        return {
            "global_max_land_usage": {
                "sheet_name": "Max_land_usage_global",
                "value": 1e30,
                "index": pd.Index(settings.years, name="Years"),
                "columns": pd.Index(
                    settings.global_settings["Technologies_glob"].loc[
                        settings.global_settings["Technologies_glob"]["Tech_category"]
                        != "Demand"
                    ]["Technology"],
                ),
            },
        }
