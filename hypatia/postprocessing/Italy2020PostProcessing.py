from hypatia.postprocessing.PostProcessingInterface import PostProcessingInterface
from hypatia.utility.constants import ModelMode
from hypatia.utility.utility import get_emission_types
from datetime import (
    datetime,
    timedelta
)
import pandas as pd
import numpy as np
import os
from typing import Dict
import os
import shutil
from hypatia.error_log.Exceptions import (
    WrongInputMode,
    DataNotImported,
    ResultOverWrite,
    SolverNotFound,
)


class Italy2020PostProcessing(PostProcessingInterface):
    def year_slice_index(
        years, time_fraction,
    ):
        try:
            return pd.MultiIndex.from_product(
                [years, time_fraction],
                names=["Years", "Timesteps"],
            )
        except TypeError:
            return pd.MultiIndex.from_product(
                [years, [1]],
                names=["Years", "Timesteps"],
            )

    def process_results(self) -> Dict:
        return {
            "tech_production": self.tech_carrier_out_production(),
            "tech_use": self.tech_carrier_in_production(),
            "tech_cost": self.tech_cost(),
            "actualized_total_cost": self.actualized_cost(),
            "emissions": self.emission(),
            "captured_emissions": self.emissions_captured(),
            "actualized_emission": self.actualized_emissions(),
            "total_capacity": self.total_capacity(),
            "new_capacity": self.new_capacity(),
            "real_new_capacity": self.real_new_capacity(),
            "storage_SOC": self.state_of_charge()
        }


    def tech_to_carrier_out(self):
        years = self._settings.years
        time_fraction = self._settings.time_steps
        year_slice = Italy2020PostProcessing.year_slice_index(years, time_fraction)
        tech_to_carriers = {}
        for region in self._settings.regions:
            carrier_out = self._settings.regional_settings[region]["Carrier_output"]
            tech_to_carriers[region] = {}
            for tech_type, techs in self._settings.regional_settings[region]["Technologies"].items():
                for tech in set(techs):
                    carriers = set(carrier_out.loc[carrier_out["Technology"] == tech]["Carrier_out"])
                    if len(carriers) == 1:
                        tech_to_carriers[region][tech] = pd.DataFrame(
                            data=[1]*(len(years)*len(time_fraction)),
                            index=year_slice,
                            columns=pd.Index(list(carriers), name="Technology")
                        )
                    elif len(carriers) > 1:
                        carrier_ratio_out = self._regional_parameters[region]["carrier_ratio_out"]
                        tech_to_carriers[region][tech] = carrier_ratio_out[tech]

        return tech_to_carriers

    def tech_to_carrier_in(self):
        years = self._settings.years
        time_fraction = self._settings.time_steps
        year_slice = Italy2020PostProcessing.year_slice_index(years, time_fraction)
        tech_to_carriers = {}
        for region in self._settings.regions:
            carrier_out = self._settings.regional_settings[region]["Carrier_input"]
            tech_to_carriers[region] = {}
            for tech_type, techs in self._settings.regional_settings[region]["Technologies"].items():
                for tech in set(techs):
                    carriers = set(carrier_out.loc[carrier_out["Technology"] == tech]["Carrier_in"])
                    if len(carriers) == 1:
                        tech_to_carriers[region][tech] = pd.DataFrame(
                            data=[1]*(len(years)*len(time_fraction)),
                            index=year_slice,
                            columns=pd.Index(list(carriers), name="Technology")
                        )
                    elif len(carriers) > 1:
                        carrier_ratio_in = self._regional_parameters[region]["carrier_ratio_in"]
                        tech_to_carriers[region][tech] = carrier_ratio_in[tech]

        return tech_to_carriers

    def tech_carrier_out_production(self):
        years = self._settings.years
        time_steps = self._settings.time_steps
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        time_fractions = {
            row.Timeslice:row.Timeslice_fraction for _, row in self._settings.global_settings["Timesteps"].iterrows()
        }

        year_slice = Italy2020PostProcessing.year_slice_index(years, time_steps)
        results = self._model_results

        # reg1, year, timeslice, tech, carrier_out, prod
        result = None
        for region in self._settings.regions:
            for tech_type, techs in self._settings.technologies[region].items():
                if(tech_type == "Demand"):
                    continue
                columns = self._settings.technologies[region][tech_type]
                frame = pd.DataFrame(
                    data=results.technology_prod[region][tech_type].value,
                    index=year_slice,
                    columns=columns,
                )
                for tech in techs:
                    res = self.tech_to_carrier_out()[region][tech].mul(frame[tech].values, axis='index')
                    res = pd.concat({tech: res}, names=['Technology'])
                    res = pd.concat({region: res}, names=['Region'])
                    res["Year"] = res.apply(
                        lambda row: datetime.strptime(str(year_to_year_name[row.name[2]]), '%Y').strftime("%Y") ,
                        # + timedelta(minutes=(525600  * time_fractions[int(row.name[3])] * (int(row.name[3]) - 1))),
                        axis=1
                    )
                    res = res.reset_index()
                    res = res.melt(
                        id_vars=['Year', 'Years', 'Timesteps', 'Region', "Technology"],
                        var_name="Carrier",
                        value_name="Value",
                    )
                    if result is None:
                        result = res
                    else:
                        result = pd.concat([result, res])
        return result.reset_index()[["Year", "Timesteps", "Region", "Technology", "Carrier", "Value"]]


    def tech_carrier_in_production(self):
        years = self._settings.years
        time_steps = self._settings.time_steps
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        time_fractions = {
            row.Timeslice:row.Timeslice_fraction for _, row in self._settings.global_settings["Timesteps"].iterrows()
        }
        year_slice = Italy2020PostProcessing.year_slice_index(years, time_steps)
        results = self._model_results

        # reg1, year, timeslice, tech, carrier_out, prod
        result = None
        for region in self._settings.regions:
            for tech_type, techs in self._settings.technologies[region].items():
                if(tech_type == "Demand" or tech_type == "Supply"):
                    continue
                columns = self._settings.technologies[region][tech_type]
                frame = pd.DataFrame(
                    data=results.technology_use[region][tech_type].value,
                    index=year_slice,
                    columns=columns,
                )
                for tech in techs:
                    res = self.tech_to_carrier_in()[region][tech].mul(frame[tech].values, axis='index')
                    res = pd.concat({tech: res}, names=['Technology'])
                    res = pd.concat({region: res}, names=['Region'])
                    res["Year"] = res.apply(
                        lambda row: datetime.strptime(str(year_to_year_name[row.name[2]]), '%Y').strftime("%Y") ,
                        # + timedelta(minutes=(525600  * time_fractions[int(row.name[3])] * (int(row.name[3]) - 1))),
                        axis=1
                    )
                    res = res.reset_index()
                    res = res.melt(
                        id_vars=['Year', 'Years', 'Timesteps', 'Region', "Technology"],
                        var_name="Carrier",
                        value_name="Value",
                    )
                    if result is None:
                        result = res
                    else:
                        result = pd.concat([result, res])
        return result.reset_index()[["Year", "Timesteps", "Region", "Technology", "Carrier", "Value"]]
    
    def state_of_charge(self):
        years = self._settings.years
        time_steps = self._settings.time_steps
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        time_fractions = {
            row.Timeslice:row.Timeslice_fraction for _, row in self._settings.global_settings["Timesteps"].iterrows()
        }
        year_slice = Italy2020PostProcessing.year_slice_index(years, time_steps)
        results = self._model_results

        # reg1, year, timeslice, tech, carrier_out, prod
        result = None
        for region in self._settings.regions:
            for tech_type, techs in self._settings.technologies[region].items():
                if(tech_type != "Storage"):
                    continue
                columns = self._settings.technologies[region][tech_type]
                frame = pd.DataFrame(
                    data=results.storage_SOC[region].value,
                    index=year_slice,
                    columns=columns,
                )
                for tech in techs:
                    res = self.tech_to_carrier_in()[region][tech].mul(frame[tech].values, axis='index')
                    res = pd.concat({tech: res}, names=['Technology'])
                    res = pd.concat({region: res}, names=['Region'])
                    res["Year"] = res.apply(
                        lambda row: datetime.strptime(str(year_to_year_name[row.name[2]]), '%Y').strftime("%Y") ,
                        # + timedelta(minutes=(525600  * time_fractions[int(row.name[3])] * (int(row.name[3]) - 1))),
                        axis=1
                    )
                    res = res.reset_index()
                    res = res.melt(
                        id_vars=['Year', 'Years', 'Timesteps', 'Region', "Technology"],
                        var_name="Carrier",
                        value_name="Value",
                    )
                    if result is None:
                        result = res
                    else:
                        result = pd.concat([result, res])
        return result.reset_index()[["Year", "Timesteps", "Region", "Technology", "Carrier", "Value"]]

    def tech_cost(self):
        years = self._settings.years
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        results = self._model_results
        costs_metrics = {
            "fixed_cost": results.cost_fix,
            "variable_cost": results.cost_variable,
            "fix_tax_cost": results.cost_fix_tax,
            "fix_sub_cost": results.cost_fix_sub,
        }
        for emission_type in get_emission_types(self._settings.global_settings):
            costs_metrics[emission_type + "_emission_cost"] = results.emission_cost_by_type[emission_type]

        if self._settings.mode == ModelMode.Planning:
            costs_metrics["decommissioning_cost"] = results.cost_decom
            costs_metrics["investment_cost"] = results.cost_inv
            costs_metrics["investment_cost_tax"] = results.cost_inv_tax
            costs_metrics["investment_cost_sub"] = results.cost_inv_sub

        result = None
        for cost_name, cost_metric in costs_metrics.items():
            for region, regional_cost in cost_metric.items():
                for tech_category, costs in regional_cost.items():
                    columns = self._settings.technologies[region][tech_category]
                    tech_costs = pd.DataFrame(
                        data=costs.value,
                        index=pd.Index(
                            years, name="Year"
                        ),
                        columns=columns,
                    )
                    tech_costs = pd.concat({region: tech_costs}, names=['Region'])
                    tech_costs["Datetime"] = tech_costs.apply(
                        lambda row: datetime.strptime(str(year_to_year_name[row.name[1]]), '%Y').strftime("%Y"),
                        axis=1
                    )
                    tech_costs = tech_costs.reset_index()
                    tech_costs = tech_costs.melt(
                        id_vars=["Year", "Datetime", "Region"],
                        var_name="Technology",
                        value_name=cost_name,
                    )
                    tech_costs = tech_costs.melt(
                        id_vars=["Year", "Datetime", "Region", "Technology"],
                        var_name="Cost",
                        value_name="Value",
                    )
                    if result is None:
                        result = tech_costs
                    else:
                        result = pd.concat([result, tech_costs])
        return result.reset_index()[["Datetime", "Region", "Technology", "Cost", "Value"]]
    
    def actualized_cost(self):
        years = self._settings.years
        results = self._model_results
        tech_costs_act = pd.DataFrame(
            data=results.totalcost_allregions_act.value,
            index=pd.Index(
                years, name="Year"
            ),
            columns=["Actualized cost"],
        )
        result = None
        if result is None:
            result = tech_costs_act
        else:
            result = pd.concat([result, tech_costs_act])
        return result    
    
    def emission(self):
        years = self._settings.years
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        results = self._model_results

        result = None
        for emission_type in get_emission_types(self._settings.global_settings):
            for region, regional_emissions in results.emission_by_type[emission_type].items():
                for tech_category, emissions in regional_emissions.items():
                    columns = self._settings.technologies[region][tech_category]
                    tech_emissions = pd.DataFrame(
                        data=emissions.value,
                        index=pd.Index(
                            years, name="Year"
                        ),
                        columns=columns,
                    )
                    tech_emissions = pd.concat({region: tech_emissions}, names=['Region'])
                    tech_emissions["Datetime"] = tech_emissions.apply(
                        lambda row: datetime.strptime(str(year_to_year_name[row.name[1]]), '%Y').strftime("%Y"),
                        axis=1
                    )
                    tech_emissions = tech_emissions.reset_index()
                    tech_emissions = tech_emissions.melt(
                        id_vars=["Datetime", "Year", "Region",],
                        var_name="Technology",
                        value_name=emission_type,
                    )
                    tech_emissions = tech_emissions.melt(
                        id_vars=["Datetime", "Year", "Region", "Technology"],
                        var_name="Emission",
                        value_name="Value",
                    )
                    if result is None:
                        result = tech_emissions
                    else:
                        result = pd.concat([result, tech_emissions])
        return result.reset_index()[["Datetime", "Region", "Technology", "Emission", "Value"]]
    
    def emissions_captured(self):
        years = self._settings.years
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        results = self._model_results

        result = None
        for emission_type in get_emission_types(self._settings.global_settings):
            for region, regional_emissions in results.captured_emission_by_type[emission_type].items():
                for tech_category, emissions in regional_emissions.items():
                    columns = self._settings.technologies[region][tech_category]
                    tech_emissions = pd.DataFrame(
                        data=emissions.value,
                        index=pd.Index(
                            years, name="Year"
                        ),
                        columns=columns,
                    )
                    tech_emissions = pd.concat({region: tech_emissions}, names=['Region'])
                    tech_emissions["Datetime"] = tech_emissions.apply(
                        lambda row: datetime.strptime(str(year_to_year_name[row.name[1]]), '%Y').strftime("%Y"),
                        axis=1
                    )
                    tech_emissions = tech_emissions.reset_index()
                    tech_emissions = tech_emissions.melt(
                        id_vars=["Datetime", "Year", "Region",],
                        var_name="Technology",
                        value_name=emission_type,
                    )
                    tech_emissions = tech_emissions.melt(
                        id_vars=["Datetime", "Year", "Region", "Technology"],
                        var_name="Emission",
                        value_name="Value",
                    )
                    if result is None:
                        result = tech_emissions
                    else:
                        result = pd.concat([result, tech_emissions])
        return result.reset_index()[["Datetime", "Region", "Technology", "Emission", "Value"]]
        
    
    def actualized_emissions(self):
        years = self._settings.years
        results = self._model_results
        emission_act = pd.DataFrame(
            data=results.totalemission_allregions_act.value,
            index=pd.Index(
                years, name="Year"
            ),
            columns=["Actualized emission"],
        )
        result = None
        if result is None:
            result = emission_act
        else:
            result = pd.concat([result, emission_act])
        return result
    
    def total_capacity(self):
        years = self._settings.years
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        results = self._model_results

        result = None
        for region in self._settings.regions:
            for tech_type, techs in results.totalcapacity[region].items():
                if(tech_type == "Demand"):
                    continue
                columns = self._settings.technologies[region][tech_type]
                res = pd.DataFrame(
                    data=results.totalcapacity[region][tech_type].value,
                    index=pd.Index(
                        years, name="Year"
                    ),
                    columns=columns,
                )

                res = pd.concat({region: res}, names=['Region'])
                res["Datetime"] = res.apply(
                    lambda row: datetime.strptime(str(year_to_year_name[row.name[1]]), '%Y').strftime("%Y"),
                    axis=1
                )
                
                res = res.reset_index()
                res = res.melt(
                    id_vars=['Datetime', 'Year', 'Region'],
                    var_name="Technology",
                    value_name=tech_type,
                )
                res = res.melt(
                    id_vars=["Datetime", "Year", "Region", "Technology"],
                    var_name="Tech category",
                    value_name="Value",
                )
                
                if result is None:
                    result = res
                else:
                    result = pd.concat([result, res])
        return result.reset_index()[["Datetime", "Region", "Technology", "Tech category", "Value"]]
    
    
    def new_capacity(self):
        years = self._settings.years
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        results = self._model_results

        result = None
        for region in self._settings.regions:
            for tech_type, techs in results.new_capacity[region].items():
                if(tech_type == "Demand"):
                    continue
                columns = self._settings.technologies[region][tech_type]
                res = pd.DataFrame(
                    data=results.new_capacity[region][tech_type].value,
                    index=pd.Index(
                        years, name="Year"
                    ),
                    columns=columns,
                )

                res = pd.concat({region: res}, names=['Region'])
                res["Datetime"] = res.apply(
                    lambda row: datetime.strptime(str(year_to_year_name[row.name[1]]), '%Y').strftime("%Y"),
                    axis=1
                )
                
                res = res.reset_index()
                res = res.melt(
                    id_vars=['Datetime', 'Year', 'Region'],
                    var_name="Technology",
                    value_name=tech_type,
                )
                res = res.melt(
                    id_vars=["Datetime", "Year", "Region", "Technology"],
                    var_name="Tech category",
                    value_name="Value",
                )
                
                if result is None:
                    result = res
                else:
                    result = pd.concat([result, res])
        return result.reset_index()[["Datetime", "Region", "Technology", "Tech category", "Value"]]
    
    def real_new_capacity(self):
        years = self._settings.years
        year_to_year_name = {
            row.Year:row.Year_name for _, row in self._settings.global_settings["Years"].iterrows()
        }
        results = self._model_results

        result = None
        for region in self._settings.regions:
            for tech_type, techs in results.real_new_capacity[region].items():
                if(tech_type == "Demand"):
                    continue
                columns = self._settings.technologies[region][tech_type]
                res = pd.DataFrame(
                    data=results.real_new_capacity[region][tech_type].value,
                    index=pd.Index(
                        years, name="Year"
                    ),
                    columns=columns,
                )

                res = pd.concat({region: res}, names=['Region'])
                res["Datetime"] = res.apply(
                    lambda row: datetime.strptime(str(year_to_year_name[row.name[1]]), '%Y').strftime("%Y"),
                    axis=1
                )
                
                res = res.reset_index()
                res = res.melt(
                    id_vars=['Datetime', 'Year', 'Region'],
                    var_name="Technology",
                    value_name=tech_type,
                )
                res = res.melt(
                    id_vars=["Datetime", "Year", "Region", "Technology"],
                    var_name="Tech category",
                    value_name="Value",
                )
                
                if result is None:
                    result = res
                else:
                    result = pd.concat([result, res])
        return result.reset_index()[["Datetime", "Region", "Technology", "Tech category", "Value"]]
    

def write_processed_result(postprocessed_result: Dict, path: str):
    for key, value in postprocessed_result.items():
        if isinstance(value, pd.DataFrame):
            value.to_csv(f"{path}//{key}.csv")
        else:
            new_path = f"{path}//{key}"
            os.makedirs(new_path, exist_ok=True)
            write_processed_result(value, new_path)

def italy2020_merge_results(scenarios: Dict[str, str], path: str, force_rewrite: bool = False):
    result_df_names = ["tech_production", "tech_use", "storage_SOC", "tech_cost", "emissions", "captured_emissions", "total_capacity", "new_capacity", "real_new_capacity", "actualized_total_cost", "actualized_emission"]
    results = {}
    for result_df_name in result_df_names:
        results[result_df_name] = None
        for scenario_name, scenatio_path in scenarios.items():
            old_df = pd.read_csv(
                r"{}/{}.csv".format(scenatio_path, result_df_name),
                index_col=[0],
                header=[0],
            )
            old_df = pd.concat({scenario_name: old_df}, names=['Scenario'])
            if results[result_df_name] is None:
                results[result_df_name] = old_df
            else:
                results[result_df_name] = pd.concat([results[result_df_name], old_df])#.reset_index().drop('level_1', axis=1)
        if result_df_name == "tech_production" or result_df_name == "tech_use" or result_df_name == "tech_cost" or result_df_name == "emissions" or result_df_name == "captured_emissions" or result_df_name == "total_capacity" or result_df_name == "new_capacity" or result_df_name == "real_new_capacity":      
            results[result_df_name] = results[result_df_name].reset_index().drop('level_1', axis=1)

    if os.path.exists(path):
        if not force_rewrite:
            raise ResultOverWrite(
                f"Folder {path} already exists. To over write"
                f" the parameter files, use force_rewrite=True."
            )
        else:
            shutil.rmtree(path)
    os.mkdir(path)
    
    write_processed_result(results, path)

