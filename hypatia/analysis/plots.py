# -*- coding: utf-8 -*-
"""
This module contains the functions and the class for
result visualization of hypatia model
"""

from copy import deepcopy
import pandas as pd
import numpy as np
from plotly import graph_objs as go
from plotly.subplots import make_subplots
import plotly.offline as pltly
from IPython import get_ipython
from hypatia.analysis.postprocessing import year_slice_index

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


def run_from_jupyter():
    if get_ipython() is not None:
        ipy_str = str(type(get_ipython()))
        if "zmqshell" in ipy_str:
            return True
        return False


def _plotter(fig, layout, path):

    fig.update_layout(layout)
    if run_from_jupyter():
        pltly.init_notebook_mode(connected=False)
        pltly.iplot({"data": fig.data, "layout": fig.layout})
    fig.write_html(path)


def get_data(panda_data, _format="list"):

    if _format == "list":
        try:
            return panda_data.tolist()
        except AttributeError:
            return [panda_data]
    elif _format == "numpy":
        try:
            return panda_data.values()
        except AttributeError:
            return [panda_data]


def plot(kind, **properties):

    if kind == "bar":
        return go.Bar(**properties)
    elif kind == "area":
        properties["line"] = dict(width=0)
        properties["mode"] = "lines"
        properties["stackgroup"] = "one"

        y = properties["y"]

        if np.any(y < 0):
            y_pos = y.copy()
            y_pos[y_pos < 0] = 0
            properties["y"] = y_pos
            fig = go.Scatter(**properties)

            y_neg = y.copy()
            y_neg[y_neg > 0] = 0
            properties["stackgroup"] = "two"
            properties["y"] = y_neg
            fig = go.Scatter(**properties)

            return fig

        fig = go.Scatter(**properties)

        return fig
    else:
        raise ValueError(f"{kind} is not an acceptable kind.")


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
    if mode == "sliders":
        fig.update_layout({mode: [dict(active=0, steps=steps, pad={"t": 50},)]})
    elif mode == "updatemenus":
        fig.update_layout({mode: [dict(active=0, buttons=steps, pad={"t": 50})]})
    else:
        raise ValueError("Acceptable modes are 'sliders' and 'updatemenus'.")
    return fig


def visible(step_index, aggregate):
    if not step_index:
        return True
    if aggregate:
        return True
    return False


def str2ls(inp):
    if isinstance(inp, str):
        return [inp]
    return inp


class Plotter:

    """A Plotting tool for hypatia"""

    def __init__(self, results, config, hourly_resolution):
        """
        Parameters
        ----------
        results : str, hypatia.Model
            Initializing the plotter object by csv files or directly from
            hypatia model.

        config : str
            path to the excel file defining the config of the plots such as
            colors, names, groups and more.

        hourly_resolution : boolean
            if True, hourly plots will be available else hourly plots cant be used

        """

        if isinstance(results, str):
            self._init_from_csv(results)
        else:
            self._init_from_object(results)

        self._read_config_file(config)
        self._hourly = hourly_resolution

    def _init_from_object(self, results):
        """Extracts the data for plots"""

        self.data = deepcopy(results.results)
        self.regions = deepcopy(results._StrData.regions)
        self.years = deepcopy(results._StrData.main_years)
        self.time_fraction = deepcopy(results._StrData.timeslice_fraction)
        self.techs = deepcopy(
            results._StrData.glob_mapping["Technologies_glob"]["Technology"].tolist()
        )
        self.fuels = deepcopy(
            results._StrData.glob_mapping["Carriers_glob"]["Carrier"].tolist()
        )
        self.emissions = deepcopy(
            results._StrData.glob_mapping["Emissions"]["Emission"].tolist()
        )

        reformed_sets = {}
        for region in results._StrData.regions:
            reformed_sets[region] = {}
            for key, value in results._StrData.mapping[region].items():
                reformed_sets[region][key] = value.set_index(
                    [main_index[key]], inplace=False
                )
        self.sets = reformed_sets

        self.glob_mapping = dict(
            techs=results._StrData.glob_mapping["Technologies_glob"].set_index(
                ["Technology"], inplace=False
            ),
            fuels=results._StrData.glob_mapping["Carriers_glob"].set_index(
                ["Carrier"], inplace=False
            ),
        )

        self.mapping = results._StrData.mapping

        years = results._StrData.main_years
        _years = results._StrData.glob_mapping["Years"]
        years = _years[_years["Year"].isin(years)]["Year_name"]
        time_fraction = results._StrData.time_steps
        year_slice = year_slice_index(years, time_fraction)

        for item in ["tech_residual_cap", "carrier_ratio_in", "carrier_ratio_out"]:

            self.data[item] = {}
            for reg in self.regions:
                if item not in results._StrData.data[reg]:
                    continue
                if item == "tech_residual_cap":
                    index = years
                else:
                    index = year_slice
                data = results._StrData.data[reg][item]
                self.data[item][reg] = pd.DataFrame(
                    data=data.values, index=index, columns=data.columns
                )

    def _init_from_csv(self, results):
        """Extracts the data from csv files"""
        raise NotImplementedError("Not implemented in this version")

    def _is_allowed(self, item):
        if item not in self.data:
            raise ValueError("This plot is not implementable for this specific case.")

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

    def plot_use_by_technology(
        self,
        fuel_group,
        path,
        regions="all",
        kind="bar",
        mode="updatemenus",
        aggregate=False,
    ):
        """Plots the use of fuels by technologies

        Parameters
        ----------

        fuel_group : str
            the name of the fuel group to be plotted based on value given in config file

        regions : str, Optional
            the regions to plot.

        path : str
            where to save the file + the name of the file and extension

        kind : str
            type of plot ['bar','area']

        mode : str
            the mode of plot when more than one region exists in

        """
        if regions == "all":
            regions = self.regions

        fuels = self.configs["fuels"]
        fuels = fuels[fuels["fuel_group"].isin(str2ls(fuel_group))].index

        if not len(fuels):
            raise ValueError("No fuel found for given category .")
        unit = self._take_units("fuels", fuels, "fuel_unit")
        fig = go.Figure()
        counter = []

        # define if demand and intermediate exist
        tech_type = self.glob_mapping["fuels"].loc[fuels, "Carr_type"].tolist()

        # in aggregated mode, legends will be defined for whole regions
        if aggregate:
            legends = set()
        for step_index, region in enumerate(regions):

            # Identify what techs are consuming that fuel
            carrier_tech = self.mapping[region]["Carrier_input"]
            carrier_tech = carrier_tech[carrier_tech.Carrier_in.isin(fuels)][
                "Technology"
            ].tolist()

            # in disaggregated mode, legends will be separated for regions
            if not aggregate:
                legends = set()
            if "Demand" in tech_type:
                for tt, values in (
                    self.data["demand"][region]
                    .groupby(level=0, sort=False)
                    .sum()
                    .iteritems()
                ):
                    if tt not in carrier_tech:
                        continue
                    name = self.configs["techs"].loc[tt, "tech_name"]
                    color = self.configs["techs"].loc[tt, "tech_color"]

                    fig.add_trace(
                        plot(
                            kind=kind,
                            x=values.index,
                            y=values.values,
                            name=name,
                            marker_color=color,
                            visible=visible(step_index, aggregate),
                            showlegend=False if tt in legends else True,
                        ),
                    )

                    legends.add(tt)
            for category, df in self.data["use_by_tech"][region].items():

                if category == "Conversion":
                    for tt, values in df.groupby(level=0, sort=False).sum().iteritems():

                        if tt not in carrier_tech:
                            continue
                        name = self.configs["techs"].loc[tt, "tech_name"]
                        color = self.configs["techs"].loc[tt, "tech_color"]

                        fig.add_trace(
                            plot(
                                kind=kind,
                                x=values.index,
                                y=values.values,
                                name=name,
                                marker_color=color,
                                visible=visible(step_index, aggregate),
                                showlegend=False if tt in legends else True,
                            )
                        )

                        legends.add(tt)
                if category == "Conversion_plus":

                    for tt, values in df.iteritems():

                        if tt not in carrier_tech:
                            continue

                        ratio = self.data["carrier_ratio_in"][region].loc[
                            :, (tt, slice(None))
                        ]

                        for cols, ratios in ratio.iteritems():
                            if cols[1] in fuels:

                                name = self.configs["techs"].loc[tt, "tech_name"]
                                color = self.configs["techs"].loc[tt, "tech_color"]

                                to_plot = (
                                    (values * ratios).groupby(level=0, sort=False).sum()
                                )
                                fig.add_trace(
                                    plot(
                                        kind=kind,
                                        x=to_plot.index,
                                        y=to_plot.values,
                                        name=name,
                                        marker_color=color,
                                        visible=visible(step_index, aggregate),
                                        showlegend=False if tt in legends else True,
                                    )
                                )
                                legends.add(tt)

            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        if not aggregate:
            fig = set_steps(fig, counter, mode)
        layout = {
            "title": "Use by technologies",
            "yaxis": {"title": unit},
            "xaxis": dict(tickmode="array", tickvals=values.index, dtick=1),
        }

        if kind == "bar":
            layout["barmode"] = "relative"
        _plotter(fig=fig, layout=layout, path=path)

    def plot_new_capacity(
        self,
        path,
        tech_group,
        regions="all",
        kind="bar",
        cummulative=False,
        mode="updatemenus",
        aggregate=False,
    ):
        """Plotes new capacity of a group of technologies

        Parameters
        ----------
        path : str
            the path to save the file with the file extension

        tech_group : str
            the group of the techs to be plotted

        regions : str
            the regions to be plotted

        kind : str
            kind of the plot ['bar','area']

        cummulative : boolean
            if True, plots the cummulative new capacity else will plot new capacity

        mode : str
            defines the model of plots in case multiple restions are given
        """

        self._is_allowed("new_capacity")

        if regions == "all":
            regions = self.regions
        techs = self.configs["techs"]
        techs = techs[techs["tech_group"].isin(str2ls(tech_group))].index

        if not len(techs):
            raise ValueError(f"No tech found for category {tech_group}.")
        unit = self._take_units("techs", techs, "tech_cap_unit")
        tech_type = self.glob_mapping["techs"].loc[techs]["Tech_category"]

        fig = go.Figure()
        counter = []
        if aggregate:
            legends = set()
        for step_index, region in enumerate(regions):
            if not aggregate:
                legends = set()
            for tt in tech_type.unique():
                if tt not in self.data["new_capacity"][region]:
                    continue
                to_plot = self.data["new_capacity"][region][tt]

                if cummulative:
                    to_plot = to_plot.cumsum()
                for t, values in to_plot.iteritems():
                    if t not in techs:
                        continue
                    name = self.configs["techs"].loc[t, "tech_name"]
                    color = self.configs["techs"].loc[t, "tech_color"]

                    fig.add_trace(
                        plot(
                            kind=kind,
                            name=name,
                            x=values.index,
                            y=values.values,
                            marker_color=color,
                            visible=visible(step_index, aggregate),
                            showlegend=False if t in legends else True,
                        )
                    )
                legends.add(t)
            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        layout = {
            "title": "Accumulated New Capacity" if cummulative else "New Capacity",
            "yaxis": {"title": unit},
            "xaxis": dict(tickmode="array", tickvals=values.index, dtick=1),
        }

        if not aggregate:
            fig = set_steps(fig, counter, mode)
        if kind == "bar":
            layout["barmode"] = "relative"
        _plotter(fig=fig, layout=layout, path=path)

    def plot_total_capacity(
        self,
        path,
        tech_group,
        regions="all",
        kind="bar",
        decom_cap=True,
        mode="updatemenus",
        aggregate=False,
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

        kind : str
            kind of the plot ['bar','area']

        decom_cap : boolean
            if True, will plot the total decomissioned capacities as negative numbers
        """
        try:
            self._is_allowed("decommissioned_capacity")
        except ValueError:
            decom_cap = False
        techs = self.configs["techs"]
        techs = techs[techs["tech_group"].isin(str2ls(tech_group))].index

        if regions == "all":
            regions = self.regions

        if not len(techs):
            raise ValueError(f"No tech found for category {tech_group}.")
        unit = self._take_units("techs", techs, "tech_cap_unit")
        tech_type = self.glob_mapping["techs"].loc[techs]["Tech_category"]

        fig = go.Figure()
        counter = []
        if aggregate:
            legends = set()
        for step_index, region in enumerate(regions):
            if not aggregate:
                legends = set()
            for tt in tech_type.unique():
                if tt not in self.data["total_capacity"][region]:
                    continue
                to_plot = self.data["total_capacity"][region][tt]
                residual = self.data["tech_residual_cap"][region][tt]

                to_plot = to_plot - residual

                for t, values in to_plot.iteritems():
                    if t not in techs:
                        continue
                    name = self.configs["techs"].loc[t, "tech_name"]
                    color = self.configs["techs"].loc[t, "tech_color"]

                    name = f"{name}: residual capacity"

                    fig.add_trace(
                        plot(
                            kind=kind,
                            name=name,
                            x=values.index,
                            y=residual[t],
                            marker_color=color,
                            opacity=0.3,
                            visible=visible(step_index, aggregate),
                            showlegend=False if t in legends else True,
                        )
                    )

                    legends.add(name)
                for t, values in to_plot.iteritems():
                    if t not in techs:
                        continue
                    name = self.configs["techs"].loc[t, "tech_name"]
                    color = self.configs["techs"].loc[t, "tech_color"]

                    name = f"{name}: new capacity"

                    fig.add_trace(
                        plot(
                            kind=kind,
                            name=name,
                            x=values.index,
                            y=values.values,
                            marker_color=color,
                            visible=visible(step_index, aggregate),
                            showlegend=False if name in legends else True,
                        )
                    )

                    legends.add(name)
                if decom_cap:
                    to_plot = self.data["decommissioned_capacity"][region][tt].cumsum()
                    residul_decom = residual.iloc[0, :] - residual

                    for t, values in to_plot.iteritems():
                        if t not in techs:
                            continue
                        name = self.configs["techs"].loc[t, "tech_name"]
                        color = self.configs["techs"].loc[t, "tech_color"]

                        name = f"{name}: residual capacity"

                        fig.add_trace(
                            plot(
                                kind=kind,
                                name=name,
                                x=values.index,
                                y=-residul_decom[t],
                                marker_color=color,
                                opacity=0.3,
                                visible=visible(step_index, aggregate),
                                showlegend=False if name in legends else True,
                            )
                        )
                    for t, values in to_plot.iteritems():
                        if t not in techs:
                            continue
                        name = self.configs["techs"].loc[t, "tech_name"]
                        color = self.configs["techs"].loc[t, "tech_color"]

                        name = f"{name}: new capacity"

                        fig.add_trace(
                            plot(
                                kind=kind,
                                name=name,
                                x=values.index,
                                y=-values.values,
                                marker_color=color,
                                opacity=0.5,
                                visible=visible(step_index, aggregate),
                                showlegend=False if name in legends else True,
                            )
                        )

                        legends.add(t)
            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        layout = {
            "title": "Total Capacity",
            "yaxis": {"title": unit},
            "xaxis": dict(tickmode="array", tickvals=values.index, dtick=1),
        }
        if not aggregate:
            fig = set_steps(fig, counter, mode)
        if kind == "bar":
            layout["barmode"] = "relative"
        _plotter(fig=fig, layout=layout, path=path)

    def plot_prod_by_tech(
        self,
        tech_group,
        path,
        regions="all",
        kind="bar",
        mode="updatemenus",
        aggregate=False,
    ):
        """Plots the total yearly production of techs

        Parameters
        ----------
        tech_group : str
            The tech_group to plot

        regions : list
            The  region/regions to plot

        kind : str
            type of the plot: [bar,area]

        path : str
            Defines the path to save the file with the extension of the file
        """

        if regions == "all":
            regions = self.regions

        techs = self.configs["techs"]
        techs = techs[techs["tech_group"].isin(str2ls(tech_group))].index

        if not len(techs):
            raise ValueError(f"No tech found for category {tech_group}.")
        unit = self._take_units("techs", techs, "tech_production_unit")
        tech_type = self.glob_mapping["techs"].loc[techs]["Tech_category"]

        fig = go.Figure()
        counter = []

        if aggregate:
            legends = set()
        for step_index, region in enumerate(regions):
            if not aggregate:
                legends = set()
            for tt in tech_type.unique():
                if tt not in self.data["production_by_tech"][region]:
                    continue
                to_plot = (
                    self.data["production_by_tech"][region][tt]
                    .groupby(level=0, sort=False)
                    .sum()
                )

                for t, values in to_plot.iteritems():
                    if t not in techs:
                        continue
                    name = self.configs["techs"].loc[t, "tech_name"]
                    color = self.configs["techs"].loc[t, "tech_color"]

                    fig.add_trace(
                        plot(
                            kind=kind,
                            name=name,
                            x=values.index,
                            y=values.values,
                            marker_color=color,
                            visible=visible(step_index, aggregate),
                            showlegend=False if t in legends else True,
                        )
                    )

                    legends.add(t)
            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        layout = {
            "title": "Production by technology",
            "yaxis": {"title": unit},
            "xaxis": dict(tickmode="array", tickvals=values.index, dtick=1),
        }
        if not aggregate:
            fig = set_steps(fig, counter, mode)
        if kind == "bar":
            layout["barmode"] = "relative"
        _plotter(fig=fig, layout=layout, path=path)

    def plot_fuel_prod_cons(
        self,
        path,
        years,
        fuel_group,
        regions="all",
        trade=True,
        mode="updatemenus",
        aggregate=False,
    ):
        """Plots the share of a fuel group production and consumption

        .. note::

           data will be aggregated over the given years

        Parameters
        ----------
        years : list
            the years to be aggregaed

        regions : list
            regions to be plotted

        trade : boolean
            if True, imports and exports will be considered in production & consumption
        """
        aggregate = False
        fuels = self.configs["fuels"]
        fuels = fuels[fuels["fuel_group"].isin(str2ls(fuel_group))].index

        if regions == "all":
            regions = self.regions

        if not len(fuels):
            raise ValueError(f"No fuel found for category {fuel_group}.")
        _ = self._take_units("fuels", fuels, "fuel_unit")

        specs = [[{"type": "domain"}, {"type": "domain"}]]
        fig = make_subplots(
            rows=1, cols=2, subplot_titles=["Production", "Consumption"], specs=specs,
        )

        counter = []

        if aggregate:
            legends = set()
        # Define the production
        for step_index, region in enumerate(regions):

            if not aggregate:
                legends = set()
            prod_techs = []

            for ff in fuels:
                if ff in self.sets[region]["Carrier_output"].index:
                    prod_techs.extend(
                        get_data(
                            self.sets[region]["Carrier_output"].loc[ff, "Technology"]
                        )
                    )
            # remove the transmission
            trans = get_data(
                self.sets[region]["Technologies"].loc["Transmission", "Technology"]
            )

            for tran in trans:
                if tran in prod_techs:
                    prod_techs.remove(tran)
            # Creating production
            labels = []
            colors = []
            production = pd.Series(dtype="float64")

            for category, df in self.data["production_by_tech"][region].items():

                if category in ["Transmission", "Storage"]:
                    continue
                sliced_techs = get_data(
                    self.sets[region]["Technologies"].loc[category, "Technology"]
                )

                techs_plt = [i for i in prod_techs if i in sliced_techs]

                if category == "Conversion_plus":
                    _df = pd.Series(dtype="float64")
                    for tt, values in df.loc[years, techs_plt].iteritems():

                        activity = values

                        ratio = self.data["carrier_ratio_out"][region].loc[
                            (years, slice(None)), (tt, slice(None))
                        ]

                        res = 0
                        for cols, ratios in ratio.iteritems():
                            if cols[1] in fuels:
                                res += (activity * ratios).sum().sum()
                        _df.loc[tt] = res
                else:
                    _df = (
                        df.groupby(level=0, sort=False)
                        .sum()
                        .loc[years, techs_plt]
                        .sum()
                    )
                production = production.append(_df)

                labels.extend(
                    [self.configs["techs"].loc[tt, "tech_name"] for tt in _df.index]
                )
                colors.extend(
                    [self.configs["techs"].loc[tt, "tech_color"] for tt in _df.index]
                )

                if (trade) and ("imports" in self.data):
                    for key, value in self.data["imports"][region].items():
                        imports = (
                            value.groupby(level=0, sort=False)
                            .sum()
                            .loc[years, fuels]
                            .sum()
                            .sum()
                        )
                        production.loc[key] = imports

                        labels.append(
                            "import from "
                            + self.configs["regions"].loc[key, "region_name"]
                        )
                        colors.append(self.configs["regions"].loc[key, "region_color"])
            fig.add_trace(
                go.Pie(
                    values=production.values,
                    labels=labels,
                    visible=visible(step_index, aggregate),
                    marker=dict(colors=colors),
                    sort=False,
                ),
                1,
                1,
            )

            consumption = pd.Series(dtype="float64")
            labels = []
            colors = []
            # Identify what techs are consuming that fuel
            carrier_tech = self.mapping[region]["Carrier_input"]
            carrier_tech = carrier_tech[carrier_tech.Carrier_in.isin(fuels)][
                "Technology"
            ].tolist()
            # define if demand and intermediate exist
            tech_type = self.glob_mapping["fuels"].loc[fuels, "Carr_type"].tolist()

            if "Demand" in tech_type:
                for tt, values in (
                    self.data["demand"][region]
                    .groupby(level=0, sort=False)
                    .sum()
                    .iteritems()
                ):
                    if tt not in carrier_tech:
                        continue
                    labels.append(self.configs["techs"].loc[tt, "tech_name"])
                    colors.append(self.configs["techs"].loc[tt, "tech_color"])
                    consumption.loc[tt] = values.loc[years].sum()
            if (trade) and ("exports" in self.data):
                for key, value in self.data["exports"][region].items():
                    exports = (
                        value.groupby(level=0, sort=False)
                        .sum()
                        .loc[years, fuels]
                        .sum()
                        .sum()
                    )
                    consumption.loc[key] = exports

                    labels.append(
                        "export to " + self.configs["regions"].loc[key, "region_name"]
                    )
                    colors.append(self.configs["regions"].loc[key, "region_color"])
            for category, df in self.data["use_by_tech"][region].items():

                if category == "Conversion":
                    for tt, values in (
                        df.groupby(level=0, sort=False)
                        .sum()
                        .loc[years, :]
                        .sum()
                        .iteritems()
                    ):

                        if tt not in carrier_tech:
                            continue
                        labels.append(self.configs["techs"].loc[tt, "tech_name"])
                        colors.append(self.configs["techs"].loc[tt, "tech_color"])
                        consumption.loc[tt] = values
                elif category == "Conversion_plus":

                    for tt, values in df.loc[years, :].iteritems():

                        if tt not in carrier_tech:
                            continue
                        labels.append(self.configs["techs"].loc[tt, "tech_name"])
                        colors.append(self.configs["techs"].loc[tt, "tech_color"])

                        activity = values
                        ratio = self.data["carrier_ratio_in"][region].loc[
                            (years, slice(None)), (tt, slice(None))
                        ]

                        res = 0
                        for cols, ratios in ratio.iteritems():
                            if cols[1] in fuels:
                                res += (activity * ratios).sum()
                        consumption.loc[tt] = res
            fig.add_trace(
                go.Pie(
                    values=consumption.values,
                    labels=labels,
                    visible=visible(step_index, aggregate),
                    marker=dict(colors=colors),
                    sort=False,
                ),
                1,
                2,
            )

            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        if not aggregate:
            fig = set_steps(fig, counter, mode)
        fig.update_annotations(yshift=20, xshift=-200)
        layout = {}
        _plotter(fig=fig, layout=layout, path=path)

    def plot_emissions(
        self,
        path,
        tech_group,
        regions="all",
        kind="bar",
        mode="updatemenus",
        aggregate=False,
    ):
        """ Plots the emissions for a tech_group

        Parameters
        -----------
        path : str
            Defines the path and the name of the file to save
        tech_group : str
            the techn_group to plot based on config excel file.

        regions : list[str]
            Which regions to plot
        kind : str, optional
            Type of the plot can be area or bar. The default is "area".
        mode : str, optional
            defined the mode when multiple regions are plotted. Acceptable values are "updatemenus" and "sliders". The default is "updatemenus".
        aggregate : boolean, optional
            If True will aggregated the regions into one singel region. The default is False.
        """
        techs = self.configs["techs"]
        techs = techs[techs["tech_group"].isin(str2ls(tech_group))].index
        unit = self.configs["emissions"].loc[self.emissions[0], "emission_unit"]
        emission_name = self.configs["emissions"].loc[self.emissions[0], "emission_name"]
        

        if regions == "all":
            regions = self.regions

        if not len(techs):
            raise ValueError(f"No tech found for category {tech_group}.")
        fig = go.Figure()
        counter = []

        if aggregate:
            legends = set()
        for step_index, region in enumerate(regions):
            if not aggregate:
                legends = set()
            for df in self.data["emissions"][region].values():
                for t, values in df.iteritems():
                    if t not in techs:
                        continue
                    name = self.configs["techs"].loc[t, "tech_name"]
                    color = self.configs["techs"].loc[t, "tech_color"]

                    fig.add_trace(
                        plot(
                            kind=kind,
                            name=name,
                            x=values.index,
                            y=values.values,
                            marker_color=color,
                            visible=visible(step_index, aggregate),
                            showlegend=False if t in legends else True,
                        )
                    )
                    legends.add(t)
            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        layout = {
            "title": emission_name,
            "xaxis": dict(tickmode="array", tickvals=values.index, dtick=1),
            "yaxis_title": unit,
        }

        if not aggregate:
            fig = set_steps(fig, counter, mode)
        _plotter(fig=fig, layout=layout, path=path)

    def plot_hourly_prod_by_tech(
        self,
        path,
        tech_group,
        year,
        regions="all",
        kind="area",
        freq="h",
        function="sum",
        start="01-01 00:00:00",
        end="12-29 23:00:00",
        mode="updatemenus",
        aggregate=False,
    ):
        """Plots hourly tech production


        Parameters
        ----------
        path : str
            Defines the path and the name of the file to save
        tech_group : str
            the techn_group to plot based on config excel file.
        regions : list[str]
            Which regions to plot
        year : int,str
            hourly plot can be used for one year only
        kind : str, optional
            Type of the plot can be area or bar. The default is "area".
        freq : str, optional
            Defines the frequencey of data.Follows the pd.Datetime rules. The default is "h". for example for a 3 hours frequency '3h' should be passed.
        function : str, optional
            In case of resampling data, the function can be specified. The default is "sum".
        start : str, optional
            the starting datetime for the plot. The default is "01-01 00:00:00".
        end : str, optional
            the ending datetime for the plot. The default is "12-29 23:00:00".
        mode : str, optional
            defined the mode when multiple regions are plotted. Acceptable values are "updatemenus" and "sliders". The default is "updatemenus".
        aggregate : boolean, optional
            If True will aggregated the regions into one singel region. The default is False.

        """

        if not self._hourly:
            raise Exception("Is only applicapable with hourly resolution")

        techs = self.configs["techs"]
        techs = techs[techs["tech_group"].isin(str2ls(tech_group))].index
        if not len(techs):
            raise ValueError(f"No tech found for category {tech_group}.")

        unit = self._take_units("techs", techs, "tech_production_unit")

        if regions == "all":
            regions = self.regions

        tech_type = self.glob_mapping["techs"].loc[techs]["Tech_category"]

        fig = go.Figure()
        counter = []
        if aggregate:
            legends = set()
        if freq != "h":
            fig.update_layout({"xaxis": {"tickformat": "%b"}})
        for step_index, region in enumerate(regions):
            if not aggregate:
                legends = set()

            # add if there are some storages consumption
            to_plots = []
            for tt in tech_type.unique():

                if tt not in self.data["production_by_tech"][region]:
                    continue

                to_plots.append(
                    self.data["production_by_tech"][region][tt].loc[year].copy()
                )

                if tt == "Storage":
                    to_plots.append(
                        -self.data["use_by_tech"][region][tt].loc[year].copy()
                    )

            for to_plot in to_plots:

                # To avoid leap years,
                time_index = pd.date_range(
                    start="2011-01-01", periods=len(to_plot), freq="1h"
                )

                to_plot.index = time_index

                try:
                    to_plot = to_plot.loc[f"2011 {start}":f"2011 {end}"]
                except:
                    raise ValueError("incorrect start or end.")

                try:
                    yy = int(year) - 2011
                    to_plot.index = to_plot.index + pd.offsets.DateOffset(years=yy)
                except:
                    pass

                to_plot = to_plot.resample(freq)
                to_plot = eval(f"to_plot.{function}()")

                for t, values in to_plot.iteritems():
                    if t not in techs:
                        continue
                    name = self.configs["techs"].loc[t, "tech_name"]
                    color = self.configs["techs"].loc[t, "tech_color"]

                    fig.add_trace(
                        plot(
                            kind=kind,
                            name=name,
                            x=values.index,
                            y=values.values,
                            marker_color=color,
                            visible=visible(step_index, aggregate),
                            showlegend=False if t in legends else True,
                        )
                    )

                    legends.add(t)
            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )
        layout = {
            "title": "Hourly production by technologies",
            "yaxis": {"title": unit},
        }
        if not aggregate:
            fig = set_steps(fig, counter, mode)
        _plotter(fig=fig, layout=layout, path=path)

    def plot_regional_costs(
        self,
        path,
        regions="all",
        stacked_by="techs",
        aggregate=False,
        mode="updatemenus",
        exclude_tech_groups=[],
        exclude_cost_items=[],
    ):
        """
        

        Parameters
        ----------
        path : str
            The path to save the plot.
        regions :  list[str], optional
            regions to plot,. The default is "all".
        stacked_by : str, optional
            defines the stacking opttion. if techs, will stack techs. if items will stack to cost items. The default is "techs".
        aggregate : boolean, optional
            if True will aggregate the regions. The default is False.
        mode : str, optional
            defines the mode if multiple regions exists. The default is "updatemenus".
        exclude_tech_groups : list[str], optional
            the tech groupes to not plot. The default is [].
        exclude_cost_items : list[str], optional
            the cost items not to plot. The default is [].
        """

        cost_items = {
            "fix_cost": {"name": "Fix Cost", "color": "red"},
            "variable_cost": {"name": "Variable Cost", "color": "blue"},
            "investment_cost": {"name": "Investment Cost", "color": "green"},
            "decommissioning_cost": {"name": "Decommissioning Cost", "color": "yellow"},
            "fix_tax_cost": {"name": "Fix Tax Cost", "color": "brown"},
            "fix_subsidies": {"name": "Fix subsidies", "color": "khaki"},
        }

        techs = self.configs["techs"]
        exclude_techs = techs[
            techs["tech_group"].isin(str2ls(exclude_tech_groups))
        ].index

        if regions == "all":
            regions = self.regions

        fig = go.Figure()
        counter = []
        if aggregate:
            legends = set()

        for step_index, region in enumerate(regions):
            if not aggregate:
                legends = set()

            for cost_item, info in cost_items.items():
                if (cost_item not in self.data) or (cost_item in exclude_cost_items):
                    continue

                to_plot = pd.concat(list(self.data[cost_item][region].values()), axis=1)
                if cost_item in ["fix_subsidies"]:
                    to_plot = -to_plot

                if stacked_by == "techs":

                    for t, values in to_plot.iteritems():
                        if t in exclude_techs:
                            continue

                        name = self.configs["techs"].loc[t, "tech_name"]
                        color = self.configs["techs"].loc[t, "tech_color"]

                        fig.add_trace(
                            plot(
                                kind="bar",
                                name=name,
                                x=[values.index, [info["name"]] * len(values)],
                                y=values.values,
                                marker_color=color,
                                legendgroup=name,
                                visible=visible(step_index, aggregate),
                                showlegend=False if t in legends else True,
                            )
                        )

                        legends.add(t)

                elif stacked_by == "items":
                    for t, values in to_plot.iteritems():
                        if t in exclude_techs:
                            continue
                        name = info["name"]
                        color = info["color"]
                        tech_name = self.configs["techs"].loc[t, "tech_name"]

                        fig.add_trace(
                            plot(
                                kind="bar",
                                name=name,
                                x=[values.index, [tech_name] * len(values)],
                                y=values.values,
                                marker_color=color,
                                legendgroup=name,
                                visible=visible(step_index, aggregate),
                                showlegend=False if cost_item in legends else True,
                            )
                        )
                        legends.add(cost_item)

                else:
                    raise ValueError(
                        "acceptable stacked_by inputs are ['techs','items']"
                    )

            counter.append(
                (self.configs["regions"].loc[region, "region_name"], len(fig.data))
            )

        layout = {"barmode": "relative"}
        if not aggregate:
            fig = set_steps(fig, counter, mode)
        _plotter(fig=fig, layout=layout, path=path)
