# -*- coding: utf-8 -*-
"""
This module contains the core of the optimization model, containing
the definiton of problem (variables,constraints,objective function,...)
in CVXPY for planning and operation modes.
"""
import pandas as pd
import cvxpy as cp
import numpy as np
from collections import namedtuple
from hypatia.backend.ModelData import ModelData
from hypatia.backend.ModelVariables import ModelVariables
from hypatia.utility.constants import ModelMode
from hypatia.utility.utility import (
    invcosts,
    invcosts_annuity,
    salvage_factor,
    newcap_accumulated,
    line_newcap_accumulated,
    _calc_variable_overall,
    _calc_production_overall,
    fixcosts,
    line_varcost,
    decomcap,
    line_decomcap,
    available_resource_prod,
    annual_activity,
    storage_state_of_charge,
    get_regions_with_storage,
    storage_max_flow,
)

import logging


logger = logging.getLogger(__name__)


RESULTS = [
    "technology_prod",
    "technology_use",
    "line_import",
    "line_export",
    "new_capacity",
    "line_new_capacity",
    "cost_fix",
    "cost_variable",
    "totalcapacity",
    "cost_fix_tax",
    "cost_fix_sub",
    "emission_cost",
    "CO2_equivalent",
    "demand",
]

PLANNING_RESULTS = [
    "cost_decom",
    "decommissioned_capacity",
    "cost_inv",
    "salvage_inv",
    "cost_inv_tax",
    "cost_inv_sub",
]


class BuildModel:

    """Class that builds the variables and equations of the model

    Attributes
    -----------
    sets:
        The instance of the Readsets class for delivering the structural inputs
        including regions, technologies, years, timesteps, mapping tables

    variables: dict
        a nested dictionary of all the decision variables including the new capacity, production
        by each technology, use (consumption) by each technology, imports and exports

    """

    def __init__(self, model_data: ModelData):

        self.model_data = model_data
        self.vars = ModelVariables(self.model_data)
        self.constr = []

        timeslice_fraction = self.model_data.settings.timeslice_fraction
        if not isinstance(timeslice_fraction, int):
            timeslice_fraction.shape = (len(self.model_data.settings.time_steps), 1)
        self.timeslice_fraction = timeslice_fraction

        # calling the methods based on the defined mode by the user
        if self.model_data.settings.mode == ModelMode.Planning:
            self._constr_totalcapacity_regional()
            self._constr_newcapacity_regional()
            self._constr_balance()
            self._constr_resource_tech_availability()
            self._constr_tech_efficiency()
            self._constr_prod_annual()
            self._constr_emission_cap()
            self._constr_storage_max_min_charge()
            self._constr_storage_max_flow_in_out()
            self._set_regional_objective_planning()

            if not self.model_data.settings.multi_node:
                self._set_final_objective_singlenode()
            else:
                self._constr_totalcapacity_line()
                self._constr_totalcapacity_overall()
                self._constr_newcapacity_overall()
                self._constr_line_availability()
                self._constr_trade_balance()
                self._constr_prod_annual_overall()
                self._set_lines_objective_planning()
                self._set_final_objective_multinode()

        elif self.model_data.settings.mode == ModelMode.Operation:
            self._constr_balance()
            self._constr_resource_tech_availability()
            self._constr_tech_efficiency()
            self._constr_prod_annual()
            self._constr_emission_cap()
            self._constr_storage_max_min_charge()
            self._constr_storage_max_flow_in_out()
            self._set_regional_objective_operation()

            if not self.model_data.settings.multi_node:
                self._set_final_objective_singlenode()
            else:
                self._constr_line_availability()
                self._constr_trade_balance()
                self._constr_prod_annual_overall()
                self._set_lines_objective_operation()
                self._set_final_objective_multinode()

    def _solve(self, verbosity, solver, **kwargs):

        """
        Creates a CVXPY problem instance, if the output status is optimal,
        returns the results to the interface
        """

        objective = cp.Minimize(self.global_objective)
        problem = cp.Problem(objective, self.constr)
        problem.solve(solver=solver, verbose=verbosity, **kwargs)

        if problem.status == "optimal":

            res = RESULTS.copy()
            to_add = []
            if self.model_data.settings.multi_node:
                if self.model_data.settings.mode == ModelMode.Planning:
                    to_add = [
                        "line_totalcapacity",
                        "line_decommissioned_capacity",
                        "cost_inv_line",
                        "cost_fix_line",
                        "cost_decom_line",
                        "cost_variable_line",
                    ]
                else:
                    to_add = [
                        "line_totalcapacity",
                        "cost_fix_line",
                        "cost_variable_line",
                    ]
            if self.model_data.settings.mode == ModelMode.Planning:
                to_add.extend(PLANNING_RESULTS)

            res.extend(to_add)
            result_collector = namedtuple("result", res)
            results = result_collector(
                **{result: getattr(self.vars, result) for result in res}
            )

            return results

        else:
            print(
                "No solution found and no result will be uploaded to the model",
                "critical",
            )

    def _constr_balance(self):

        """
        Ensures the energy balance of each carrier within each region
        """
        for reg in self.model_data.settings.regions:
            for carr in self.model_data.settings.global_settings["Carriers_glob"]["Carrier"]:

                self.vars.totalusebycarrier[reg][carr] = cp.reshape(
                    self.vars.totalusebycarrier[reg][carr],
                    self.vars.totalprodbycarrier[reg][carr].shape,
                )

                self.constr.append(
                    self.vars.totalprodbycarrier[reg][carr]
                    + self.vars.totalimportbycarrier[reg][carr]
                    - self.vars.totalusebycarrier[reg][carr]
                    - self.vars.totalexportbycarrier[reg][carr]
                    - self.vars.totaldemandbycarrier[reg][carr]
                    == 0
                )

    def _constr_trade_balance(self):

        """
        Ensure sthe trade balance among any pairs of regions before the transmission
        loss
        """

        for reg in self.model_data.settings.regions:

            for key in self.vars.line_import[reg].keys():

                self.constr.append(
                    self.vars.line_import[reg][key]
                    - self.vars.line_export[key][reg]
                    == 0
                )

    def _constr_resource_tech_availability(self):

        """
        Guarantees the adequecy of total capacity of each technology based on
        the technology capacity factor and resource availability
        """

        for reg in self.model_data.settings.regions:

            for key in self.vars.technology_prod[reg].keys():

                if key != "Storage":

                    for indx, year in enumerate(self.model_data.settings.years):

                        self.available_prod = available_resource_prod(
                            self.vars.totalcapacity[reg][key][indx : indx + 1, :],
                            self.model_data.regional_parameters[reg]["res_capacity_factor"]
                            .loc[(year, slice(None)), (key, slice(None))]
                            .values,
                            self.timeslice_fraction,
                            self.model_data.regional_parameters[reg]["annualprod_per_unitcapacity"]
                            .loc[:, (key, slice(None))]
                            .values,
                        )

                        self.constr.append(
                            self.available_prod
                            - self.vars.technology_prod[reg][key][
                                indx
                                * len(self.model_data.settings.time_steps) : (indx + 1)
                                * len(self.model_data.settings.time_steps),
                                :,
                            ]
                            >= 0
                        )

                        self.constr.append(
                            cp.multiply(
                                cp.sum(self.available_prod, axis=0),
                                self.model_data.regional_parameters[reg]["tech_capacity_factor"].loc[
                                    year, (key, slice(None))
                                ],
                            )
                            - cp.sum(
                                self.vars.technology_prod[reg][key][
                                    indx
                                    * len(self.model_data.settings.time_steps) : (indx + 1)
                                    * len(self.model_data.settings.time_steps),
                                    :,
                                ],
                                axis=0,
                            )
                            >= 0
                        )

    def _constr_line_availability(self):

        """
        Guarantees the adequecy of inter-regional link capacities based on their
        capacity factor
        """

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.line_import[reg].items():

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
                        capacity = self.vars.line_totalcapacity["{}-{}".format(reg, key)][
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
                        capacity = self.vars.line_totalcapacity["{}-{}".format(key, reg)][
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

                    self.constr.append(
                        cp.multiply(
                            cp.multiply(capacity, capacity_to_production),
                            self.timeslice_fraction,
                        )
                        - value[
                            indx
                            * len(self.model_data.settings.time_steps) : (indx + 1)
                            * len(self.model_data.settings.time_steps),
                            :,
                        ]
                        >= 0
                    )
                    self.constr.append(
                        cp.multiply(
                            cp.multiply(capacity, capacity_factor),
                            capacity_to_production,
                        )
                        - line_import
                        >= 0
                    )

    def _constr_totalcapacity_regional(self):

        """
        Defines the annual upper and lower limit on the total capacity
        of each technology within each region
        """
        for reg in self.model_data.settings.regions:

            for key, value in self.vars.totalcapacity[reg].items():

                self.constr.append(
                    value - self.model_data.regional_parameters[reg]["tech_mintotcap"].loc[:, key].values
                    >= 0
                )
                self.constr.append(
                    value - self.model_data.regional_parameters[reg]["tech_maxtotcap"].loc[:, key] <= 0
                )

    def _constr_totalcapacity_overall(self):

        """
        Defines the annual upper and lower limit on the aggregated total capacity
        of each technology over all the regions
        """

        self.vars.totalcapacity_overall = _calc_variable_overall(
            self.model_data.settings.global_settings["Technologies_glob"],
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.technologies,
            self.vars.totalcapacity,
        )

        for tech, value in self.vars.totalcapacity_overall.items():

            self.constr.append(
                value - self.model_data.global_parameters["global_mintotcap"].loc[:, tech].values
                >= 0
            )
            self.constr.append(
                value - self.model_data.global_parameters["global_maxtotcap"].loc[:, tech].values
                <= 0
            )

    def _constr_totalcapacity_line(self):

        """
        Defines the upper and lower limit on the annual total capacity of the
        inter-regional links
        """

        for key, value in self.vars.line_totalcapacity.items():

            self.constr.append(
                value <= self.model_data.trade_parameters["line_maxtotcap"][key].values
            )
            self.constr.append(
                value >= self.model_data.trade_parameters["line_mintotcap"][key].values
            )

    def _constr_newcapacity_regional(self):

        """
        Defines the upper and lower limit on the annual new installed capacity
        of each technology within each region
        """

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.new_capacity[reg].items():

                self.constr.append(
                    value >= self.model_data.regional_parameters[reg]["tech_min_newcap"].loc[:, key]
                )
                self.constr.append(
                    value <= self.model_data.regional_parameters[reg]["tech_max_newcap"].loc[:, key]
                )

    def _constr_newcapacity_overall(self):

        """
        Defines the upper and lower limit on the aggregated new installed capacity
        of each technology over all the regions
        """

        self.newcapacity_overall = _calc_variable_overall(
            self.model_data.settings.global_settings["Technologies_glob"],
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.technologies,
            self.vars.new_capacity,
        )

        for tech, value in self.newcapacity_overall.items():
            self.constr.append(
                value - self.model_data.global_parameters["global_min_newcap"].loc[:, tech] >= 0
            )
            self.constr.append(
                value - self.model_data.global_parameters["global_max_newcap"].loc[:, tech] <= 0
            )

    def _constr_newcapacity_line(self):

        """
        Defines the upper and lower limit on the annual new installed capacity
        of the inter-regional links
        """

        for key, value in self.vars.new_capacity.items():

            self.constr.append(value <= self.model_data.trade_parameters["line_max_newcap"][key])
            self.constr.append(value >= self.model_data.trade_parameters["line_min_newcap"][key])

    def _constr_tech_efficiency(self):

        """
        Defines the relationship between the input and output activity of
        conversion, transmission and conversion-plus technologies
        """

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.technology_prod[reg].items():

                if key != "Supply" and key != "Storage":

                    tech_efficiency_reshape = pd.concat(
                        [self.model_data.regional_parameters[reg]["tech_efficiency"][key]]
                        * len(self.model_data.settings.time_steps)
                    ).sort_index()

                    self.constr.append(
                        value
                        - cp.multiply(
                            self.vars.technology_use[reg][key],
                            tech_efficiency_reshape.values,
                        )
                        == 0
                    )

    def _constr_prod_annual(self):

        """
        Defines the upper and lower limit for the annual production of the technologies
        within each region
        """

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.technology_prod[reg].items():

                production_annual = annual_activity(
                    value, self.model_data.settings.years, self.model_data.settings.time_steps,
                )
                if key != "Transmission" and key != "Storage":

                    self.constr.append(
                        production_annual
                        - self.model_data.regional_parameters[reg]["tech_max_production"].loc[
                            :, (key, slice(None))
                        ]
                        <= 0
                    )
                    self.constr.append(
                        production_annual
                        - self.model_data.regional_parameters[reg]["tech_min_production"].loc[
                            :, (key, slice(None))
                        ]
                        >= 0
                    )

    def _constr_prod(self):

        """
        Defines the upper and lower limit for the hourly production of the technologies
        within each region
        """

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.technology_prod[reg].items():

                if key != "Transmission" and key != "Storage":

                    self.constr.append(
                        value
                        - self.model_data.regional_parameters[reg]["tech_max_production_h"].loc[
                            :, (key, slice(None))
                        ]
                        <= 0
                    )
                    self.constr.append(
                        value
                        - self.model_data.regional_parameters[reg]["tech_min_production_h"].loc[
                            :, (key, slice(None))
                        ]
                        >= 0
                    )

    def _constr_prod_annual_overall(self):

        """
        Defines the upper and lower limit for the aggregated annual production
        of the technologies over all the regions
        """

        self.production_overall = _calc_production_overall(
            self.model_data.settings.global_settings["Technologies_glob"],
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.technologies,
            self.vars.production_annual,
        )

        for tech, value in self.production_overall.items():

            self.constr.append(
                value - self.model_data.global_parameters["global_min_production"].loc[:, tech] >= 0
            )
            self.constr.append(
                value - self.model_data.global_parameters["global_max_production"].loc[:, tech] <= 0
            )

    def _constr_emission_cap(self):

        """
        Defines the CO2 emission cap within each region and over all the regions
        """
        self.regional_emission = {}
        self.global_emission = np.zeros(
            (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps), 1)
        )
        for reg in self.model_data.settings.regions:

            self.regional_emission[reg] = np.zeros(
                (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps), 1)
            )

            for key, value in self.vars.CO2_equivalent[reg].items():

                self.regional_emission[reg] += cp.sum(value, axis=1)

                emission_cap = self.model_data.regional_parameters[reg]["emission_cap_annual"].values

                emission_cap.shape = self.regional_emission[reg].shape

            self.global_emission += self.regional_emission[reg]

            self.constr.append(emission_cap - self.regional_emission[reg] >= 0)

        if len(self.model_data.settings.regions) > 1:

            global_emission_cap = self.model_data.global_parameters[
                "global_emission_cap_annual"
            ].values
            global_emission_cap.shape = self.global_emission.shape

            self.constr.append(global_emission_cap - self.global_emission >= 0)

    def _constr_storage_max_min_charge(self):

        """
        Defines the maximum and minumum alllowed storage state of charge in each
        timestep of the year based on the total nominal capacity and the minimum
        state of charge factor
        """
        for reg in get_regions_with_storage(self.model_data.settings):

            for indx, year in enumerate(self.model_data.settings.years):

                self.constr.append(
                    self.vars.totalcapacity[reg]["Storage"][indx : indx + 1, :]
                    - self.storage_SOC[reg][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    >= 0
                )

                self.constr.append(
                    self.storage_SOC[reg][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    - cp.multiply(
                        self.vars.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                        self.model_data.regional_parameters[reg]["storage_min_SOC"].values[
                            indx : indx + 1, :
                        ],
                    )
                    >= 0
                )

    def _constr_storage_max_flow_in_out(self):

        """
        Defines the maximum and minimum allowed storage inflow and outflow in each
        hour of the year based on the total capacity, the capacity factor and
        the storage charge and discharge time
        """

        for reg in get_regions_with_storage(self.model_data.settings):

            for indx, year in enumerate(self.model_data.settings.years):

                max_storage_flow_in = storage_max_flow(
                    self.vars.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                    self.model_data.regional_parameters[reg]["storage_charge_time"].values,
                    self.model_data.regional_parameters[reg]["tech_capacity_factor"]["Storage"].values[
                        indx : indx + 1, :
                    ],
                    self.timeslice_fraction,
                )

                max_storage_flow_out = storage_max_flow(
                    self.vars.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                    self.model_data.regional_parameters[reg]["storage_discharge_time"].values,
                    self.model_data.regional_parameters[reg]["tech_capacity_factor"]["Storage"].values[
                        indx : indx + 1, :
                    ],
                    self.timeslice_fraction,
                )

                self.constr.append(
                    max_storage_flow_in
                    - self.vars.technology_use[reg]["Storage"][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    >= 0
                )

                self.constr.append(
                    max_storage_flow_out
                    - self.vars.technology_prod[reg]["Storage"][
                        indx
                        * len(self.model_data.settings.time_steps) : (indx + 1)
                        * len(self.model_data.settings.time_steps),
                        :,
                    ]
                    >= 0
                )

    def _set_regional_objective_planning(self):

        """
        Calculates the regional objective function in the planning mode
        """

        self.totalcost_allregions = np.zeros((len(self.model_data.settings.years), 1))
        self.inv_allregions = 0
        years = -1 * np.arange(len(self.model_data.settings.years))

        for reg in self.model_data.settings.regions:

            totalcost_regional = np.zeros((len(self.model_data.settings.years), 1))

            for ctgry in self.model_data.settings.technologies[reg].keys():

                if ctgry != "Demand":

                    totalcost_regional += cp.sum(
                        self.vars.cost_inv_tax[reg][ctgry]
                        - self.vars.cost_inv_sub[reg][ctgry]
                        + self.vars.cost_fix[reg][ctgry]
                        + self.vars.cost_fix_tax[reg][ctgry]
                        - self.vars.cost_fix_sub[reg][ctgry]
                        + self.vars.cost_variable[reg][ctgry]
                        + self.vars.cost_decom[reg][ctgry]
                        - self.vars.salvage_inv[reg][ctgry],
                        axis=1,
                    )

                    self.inv_allregions += self.vars.cost_inv_fvalue[reg][ctgry]

                    if ctgry != "Transmission" and ctgry != "Storage":

                        totalcost_regional += cp.sum(
                            self.vars.emission_cost[reg][ctgry], axis=1
                        )

            discount_factor = (
                1 + self.model_data.regional_parameters[reg]["discount_rate"]["Annual Discount Rate"].values
            )

            totalcost_regional_discounted = cp.multiply(
                totalcost_regional, np.power(discount_factor, years)
            )
            self.totalcost_allregions += totalcost_regional_discounted

    def _set_regional_objective_operation(self):

        """
        Calculates the regional objective function in the operation mode
        """
        self.totalcost_allregions = 0
        for reg in self.model_data.settings.regions:

            totalcost_regional = 0

            for ctgry in self.model_data.settings.technologies[reg].keys():

                if ctgry != "Demand":

                    totalcost_regional += cp.sum(
                        self.vars.cost_fix[reg][ctgry]
                        + self.vars.cost_fix_tax[reg][ctgry]
                        - self.vars.cost_fix_sub[reg][ctgry]
                        + self.vars.cost_variable[reg][ctgry]
                    )

                    if ctgry != "Transmission" and ctgry != "Storage":

                        totalcost_regional += cp.sum(
                            self.vars.emission_cost[reg][ctgry], axis=1
                        )

            self.totalcost_allregions += totalcost_regional

    def _set_lines_objective_planning(self):

        """
        Calculates the objective function of the inter-regional links in the
        planning mode
        """

        years = -1 * np.arange(len(self.model_data.settings.years))
        self.totalcost_lines = np.zeros((len(self.model_data.settings.years), 1))

        for line in self.model_data.settings.lines_list:

            self.totalcost_lines += cp.sum(
                self.vars.cost_inv_line[line]
                + self.vars.cost_fix_line[line]
                + self.vars.cost_decom_line[line],
                axis=1,
            )

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.cost_variable_line[reg].items():

                self.totalcost_lines += cp.sum(value, axis=1)

        discount_factor_global = (
            1
            + self.model_data.global_parameters["global_discount_rate"][
                "Annual Discount Rate"
            ].values
        )

        self.totalcost_lines_discounted = cp.multiply(
            self.totalcost_lines, np.power(discount_factor_global, years)
        )

    def _set_lines_objective_operation(self):

        """
        Calculates the objective function of the inter-regional links in the
        operation mode
        """

        self.totalcost_lines = np.zeros((len(self.model_data.settings.years), 1))

        for line in self.model_data.settings.lines_list:

            self.totalcost_lines += cp.sum(self.vars.cost_fix_line[line], axis=1)

        for reg in self.model_data.settings.regions:

            for key, value in self.vars.cost_variable_line[reg].items():

                self.totalcost_lines += cp.sum(value, axis=1)

    def _set_final_objective_singlenode(self):

        """
        Calculates the overall objective function in a single-node model
        """
        if self.model_data.settings.mode == ModelMode.Planning:
            self.global_objective = (
                cp.sum(self.totalcost_allregions) + self.inv_allregions
            )

        elif self.model_data.settings.mode == ModelMode.Operation:

            self.global_objective = self.totalcost_allregions

    def _set_final_objective_multinode(self):

        """
        Calculates the overall objective function as the summation of all the
        regional and inter-regional links objective functions in a multi-node
        model
        """

        if self.model_data.settings.mode == ModelMode.Planning:

            self.global_objective = (
                cp.sum(self.totalcost_lines_discounted + self.totalcost_allregions)
                + self.inv_allregions
            )

        elif self.model_data.settings.mode == ModelMode.Operation:

            self.global_objective = self.totalcost_allregions + self.totalcost_lines
