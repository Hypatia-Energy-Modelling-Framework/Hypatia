# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 11:37:11 2022

@author: NAMAZIFN
"""
import pandas as pd
from copy import deepcopy
from plotly import graph_objs as go
from hypatia import Sensitivity


def str2ls(inp):
    if isinstance(inp, str):
        return [inp]
    return inp

CARS = "Carriers"
TECHS = "Technologies"
CARS_IN = "Carrier_input"
CARS_OUT = "Carrier_output"

main_index = {
    CARS: "Carr_type",
    TECHS: "Tech_category",
    CARS_IN: "Carrier_in",
    CARS_OUT: "Carrier_out",
}

def year_slice_index(
    years, time_fraction,
):

    try:
        return pd.MultiIndex.from_product([years, time_fraction],)
    except TypeError:
        return pd.MultiIndex.from_product([years, [1]])

def visible(reg_index):
    if not reg_index:
        return True
    return False

def set_steps(fig, counter, mode):

    steps = []
    for name, step_upper in counter:
        if name == counter[0][0]:
            step_lower = 0
        steps.append(
            dict(
                label=name,
                method="update",
                args=[
                    {
                        "visible": [
                            True if step_lower <= i < step_upper else False
                            for i in range(len(fig.data))
                        ]
                    }
                ],
            )
        )

        step_lower = step_upper
        
        if mode == "updatemenus":
            fig.update_layout({mode: [dict(active=0, buttons=steps, pad={"t": 50})]})
    
    return fig

class HyPlot:
    
    """A Plotting class for BE-HyFE project"""

    def __init__(self, model, results_path, config, sample_N, hourly_resolution,sens):
        """
        Parameters
        ----------
        model : hypatia.Model
            The object of hypatia Model to pass some reguired settings
            
        results_path : str
            path to the results folder containg the csv files

        config : str
            path to the excel file defining the config of the plots such as
            colors, names, groups and more.

        hourly_resolution : boolean
            if True, hourly plots will be available else hourly plots cant be used
            
        """
        self.sens = sens
        self._read_config_file(config)
        self._take_settings(model)
        self._hourly = hourly_resolution
        self.sample_N = sample_N
        self.results_path = results_path
        self._read_csv_files(results_path,sample_N,model)

        
    def _read_config_file(self, config):
        """Reads the config file and checks the consistency"""
        configs = {}
        for sheet in ["Techs", "Fuels", "Regions", "Emissions"]:
            data = pd.read_excel(io=config, sheet_name=sheet, index_col=0, header=0,)

            if data.isnull().values.any():
                raise Exception(
                    f"nans are not acceptable in the config file. sheet_name = {sheet}"
                )
            configs[sheet.lower()] = data
        self.configs = configs
        
    
    def _read_csv_files(self,results_path,sample_N,model):
        
        results_csv = {}
        
        for samp_result in range(sample_N*(2*len(self.sens._parameters)+2)):
            
            results_csv['results_{}'.format(samp_result)] = {}
            
            for param, param_value in model.results.items():
                
                results_csv['results_{}'.format(samp_result)][param]={}
                
                for reg_line, final_value in param_value.items():
                    
                    if isinstance(final_value,pd.DataFrame):
                        
                        results_csv['results_{}'.format(samp_result)][param][reg_line] =\
                            pd.read_csv(r'{}/results_{}/{}/{}.csv'.format(results_path,samp_result,param,reg_line),
                                        index_col = 0, header = 0)
    
                                        
                    else:
                        
                        results_csv['results_{}'.format(samp_result)][param][reg_line]={}
                        
                        for tt,value in final_value.items():
                            
                            results_csv['results_{}'.format(samp_result)][param][reg_line][tt] =\
                                pd.read_csv(r'{}/results_{}/{}/{}/{}.csv'.format(results_path,samp_result,param,reg_line,tt),
                                            index_col = 0, header = 0)
                                
        self.results_csv = results_csv

    def _take_units(self, _set, item, level):

        try:
            units = self.configs[_set].loc[item, level].unique()
        except AttributeError:
            units = [self.configs[_set].loc[item, level]]
        if len(units) != 1:
            raise Exception(
                "items with different units cant be plotted. "
                f"items {item} have multiple units {units}."
            )
        return units[0]

    def _take_settings(self, model):
        """Extracts the data for plots"""

        self.data = deepcopy(model.results)
        self.regions = deepcopy(model._StrData.regions)
        self.time_fraction = deepcopy(model._StrData.timeslice_fraction)
        self.techs = deepcopy(
            model._StrData.glob_mapping["Technologies_glob"]["Technology"].tolist()
        )
        self.fuels = deepcopy(
            model._StrData.glob_mapping["Carriers_glob"]["Carrier"].tolist()
        )
        self.emissions = deepcopy(
            model._StrData.glob_mapping["Emissions"]["Emission"].tolist()
        )

        reformed_sets = {}
        for region in model._StrData.regions:
            reformed_sets[region] = {}
            for key, value in model._StrData.mapping[region].items():
                reformed_sets[region][key] = value.set_index(
                    [main_index[key]], inplace=False
                )
        self.sets = reformed_sets

        self.glob_mapping = dict(
            techs=model._StrData.glob_mapping["Technologies_glob"].set_index(
                ["Technology"], inplace=False
            ),
            fuels=model._StrData.glob_mapping["Carriers_glob"].set_index(
                ["Carrier"], inplace=False
            ),
        )

        self.mapping = model._StrData.mapping

        self.years = deepcopy(model._StrData.main_years)
        _years = model._StrData.glob_mapping["Years"]
        self.years = list(_years[_years["Year"].isin(self.years)]["Year_name"])
        time_fraction = model._StrData.time_steps
        year_slice = year_slice_index(self.years, time_fraction)

           

    def _sort_data(self,parameter,regions):
        
        
        plot_input = {}
        
        for reg in self.regions:
            concat_dict = {}
            for samp_result in self.results_csv:
                concat_dict[samp_result] = pd.concat(list(self.results_csv[samp_result][parameter][reg].values()),axis=1) 
                
            plot_input[reg] = pd.concat(concat_dict,axis=0)
            idx = plot_input[reg].index.sortlevel(-1)[0]
            plot_input[reg] = plot_input[reg].loc[idx]
                
        return plot_input
                

    def plot_total_capacity(
        self,
        path,
        tech_group,
        regions="all",
        mode="updatemenus"
    ):
        """Plots operative total capacity and total decomissioned capacity

        .. note::
            residual capacities are plotted with the same color but with lower opacity

        Parameters
        ----------
        path : str
            path to save the plot with the extension

        tech_group : str
            the group of the techs to be plotted

        regions : str
            the regions to be plotted

        """
        
        
        techs = self.configs["techs"]
        techs = list(techs[techs["tech_group"].isin(str2ls(tech_group))].index)
    
        if regions == "all":
            regions = self.regions
    
        if not len(techs):
            raise ValueError(f"No tech found for category {tech_group}.")
        unit = self._take_units("techs", techs, "tech_cap_unit")
        tech_type = self.glob_mapping["techs"].loc[techs]["Tech_category"]
        x = sorted(self.years*self.sample_N*(2*len(self.sens._parameters)+2))
        
        
        fig = go.Figure()
        counter = []
        capacity_plot_input = self._sort_data('total_capacity',self.regions)
        for reg_index, region in enumerate(regions):
            legends = set()
            for t in capacity_plot_input[region].columns:
                if t not in techs:
                    continue
                
                name = self.configs["techs"].loc[t, "tech_name"]
                color = self.configs["techs"].loc[t, "tech_color"]

                fig.add_trace(
                    go.Box(
                        name=name,
                        x=x,
                        y=capacity_plot_input[region].loc[:,t].values,
                        marker_color=color,
                        visible=visible(reg_index),
                        showlegend=False if t in legends else True,
                    )
                )
                
                legends.add(name)
            
            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data)))
               
        fig.update_layout(
            title = 'Sensitivity Analysis on Hydrogen Supply Technologies',
            yaxis_title = unit,
            xaxis = {'dtick' : 1},
            boxmode='group',
            showlegend = True)
        
        fig = set_steps(fig, counter, mode)
                    
        fig.write_html(path)