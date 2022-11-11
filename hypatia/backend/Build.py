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
    "variables",
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

    def __init__(self, sets):

        self.sets = sets
        self.constr = []
        timeslice_fraction = self.sets.timeslice_fraction
        if not isinstance(timeslice_fraction, int):
            timeslice_fraction.shape = (len(self.sets.time_steps), 1)
        self.timeslice_fraction = timeslice_fraction

        self._set_variables()

        # calling the methods based on the defined mode by the user
        if self.sets.mode == "Planning":

            self._calc_variable_planning()
            self._balance_()
            self._constr_totalcapacity_regional()
            self._constr_newcapacity_regional()
            self._constr_balance()
            self._constr_resource_tech_availability()
            self._constr_tech_efficiency()
            self._constr_prod_annual()
            self._constr_emission_cap()
            self._calc_variable_storage_SOC()
            self._constr_storage_max_min_charge()
            self._constr_storage_max_flow_in_out()
            self._set_regional_objective_planning()

            if len(self.sets.regions) == 1:
                self._set_final_objective_singlenode()

            elif len(self.sets.regions) > 1:

                self._calc_variable_planning_line()
                self._constr_totalcapacity_line()
                self._constr_totalcapacity_overall()
                self._constr_newcapacity_overall()
                self._constr_line_availability()
                self._constr_trade_balance()
                self._constr_prod_annual_overall()
                self._set_lines_objective_planning()
                self._set_final_objective_multinode()

        elif self.sets.mode == "Operation":

            self._calc_variable_operation()
            self._balance_()
            self._constr_balance()
            self._constr_resource_tech_availability()
            self._constr_tech_efficiency()
            self._constr_prod_annual()
            self._constr_emission_cap()
            self._calc_variable_storage_SOC()
            self._constr_storage_max_min_charge()
            self._constr_storage_max_flow_in_out()
            self._set_regional_objective_operation()

            if len(self.sets.regions) == 1:
                self._set_final_objective_singlenode()

            elif len(self.sets.regions) > 1:

                self._calc_variable_operation_line()
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

            # Reshape the demand
            self.demand = {
                reg: self.sets.data[reg]["demand"] for reg in self.sets.regions
            }

            res = RESULTS.copy()
            to_add = []
            if self.sets.multi_node:
                if self.sets.mode == "Planning":
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
            if self.sets.mode == "Planning":
                to_add.extend(PLANNING_RESULTS)

            res.extend(to_add)
            result_collector = namedtuple("result", res)
            results = result_collector(
                **{result: getattr(self, result) for result in res}
            )

            return results

        else:
            print(
                "No solution found and no result will be uploaded to the model",
                "critical",
            )

    def _set_variables(self):

        """
        Creates the matrixed-based variables of the problem
        in a nested dict format for each region and each technology category.
        """

        technology_prod = {}
        technology_use = {}
        new_capacity = {}
        line_newcapacity = {}
        line_import = {}
        line_export = {}

        for reg in self.sets.regions:
            regional_prod = {}
            regional_use = {}
            for key in self.sets.Technologies[reg].keys():

                if key != "Demand":

                    regional_prod[key] = cp.Variable(
                        shape=(
                            len(self.sets.main_years) * len(self.sets.time_steps),
                            len(self.sets.Technologies[reg][key]),
                        ),
                        nonneg=True,
                    )
                if key != "Demand" and key != "Supply":
                    regional_use[key] = cp.Variable(
                        shape=(
                            len(self.sets.main_years) * len(self.sets.time_steps),
                            len(self.sets.Technologies[reg][key]),
                        ),
                        nonneg=True,
                    )

            technology_prod[reg] = regional_prod
            technology_use[reg] = regional_use

            export_ = {}
            import_ = {}
            for reg_ in self.sets.regions:

                if reg_ != reg:
                    export_[reg_] = cp.Variable(
                        shape=(
                            len(self.sets.main_years) * len(self.sets.time_steps),
                            len(self.sets.glob_mapping["Carriers_glob"].index),
                        ),
                        nonneg=True,
                    )
                    import_[reg_] = cp.Variable(
                        shape=(
                            len(self.sets.main_years) * len(self.sets.time_steps),
                            len(self.sets.glob_mapping["Carriers_glob"].index),
                        ),
                        nonneg=True,
                    )

            line_export[reg] = export_
            line_import[reg] = import_

        self.variables = {
            "productionbyTechnology": technology_prod,
            "usebyTechnology": technology_use,
        }

        if len(self.sets.regions) > 1:

            self.variables.update(
                {"line_export": line_export, "line_import": line_import,}
            )

        if self.sets.mode == "Planning":

            for reg in self.sets.regions:
                regional_newcap = {}
                for key in self.sets.Technologies[reg].keys():

                    if key != "Demand":

                        regional_newcap[key] = cp.Variable(
                            shape=(
                                len(self.sets.main_years),
                                len(self.sets.Technologies[reg][key]),
                            ),
                            nonneg=True,
                        )

                new_capacity[reg] = regional_newcap

            self.variables.update({"newcapacity": new_capacity})

            if len(self.sets.regions) > 1:

                for line in self.sets.lines_list:

                    line_newcapacity[line] = cp.Variable(
                        shape=(
                            len(self.sets.main_years),
                            len(self.sets.glob_mapping["Carriers_glob"].index),
                        ),
                        nonneg=True,
                    )

                self.variables.update({"line_newcapacity": line_newcapacity})

    def _calc_variable_planning(self):

        """
        Calculates all the cost components of the objective function and the
        intermediate variables in the planning mode, for each region
        """

        self.cost_inv = {}
        self.cost_inv_tax = {}
        self.cost_inv_sub = {}
        self.cost_inv_fvalue = {}
        self.salvage_inv = {}
        self.accumulated_newcapacity = {}
        self.totalcapacity = {}
        self.cost_fix = {}
        self.cost_fix_tax = {}
        self.cost_fix_sub = {}
        self.decommissioned_capacity = {}
        self.cost_decom = {}
        self.cost_variable = {}
        self.CO2_equivalent = {}
        self.emission_cost = {}
        self.production_annual = {}

        for reg in self.sets.regions:

            cost_inv_regional = {}
            cost_inv_tax_regional = {}
            cost_inv_sub_regional = {}
            cost_fvalue_regional = {}
            salvage_inv_regional = {}
            accumulated_newcapacity_regional = {}
            totalcapacity_regional = {}
            cost_fix_regional = {}
            cost_fix_tax_regional = {}
            cost_fix_Sub_regional = {}
            decomcapacity_regional = {}
            cost_decom_regional = {}
            cost_variable_regional = {}
            CO2_equivalent_regional = {}
            emission_cost_regional = {}
            production_annual_regional = {}

            for key in self.variables["newcapacity"][reg].keys():

                (
                    cost_inv_regional[key],
                    cost_inv_tax_regional[key],
                    cost_inv_sub_regional[key],
                ) = invcosts(
                    self.sets.data[reg]["tech_inv"][key],
                    self.variables["newcapacity"][reg][key],
                    self.sets.data[reg]["inv_taxsub"]["Tax"][key],
                    self.sets.data[reg]["inv_taxsub"]["Sub"][key],
                )

                salvage_inv_regional[key] = cp.multiply(
                    salvage_factor(
                        self.sets.main_years,
                        self.sets.Technologies[reg][key],
                        self.sets.data[reg]["tech_lifetime"].loc[:, key],
                        self.sets.data[reg]["interest_rate"].loc[:, key],
                        self.sets.data[reg]["discount_rate"],
                        self.sets.data[reg]["economic_lifetime"].loc[:, key],
                    ),
                    cost_inv_regional[key],
                )

                accumulated_newcapacity_regional[key] = newcap_accumulated(
                    self.variables["newcapacity"][reg][key],
                    self.sets.Technologies[reg][key],
                    self.sets.main_years,
                    self.sets.data[reg]["tech_lifetime"].loc[:, key],
                )

                totalcapacity_regional[key] = (
                    accumulated_newcapacity_regional[key]
                    + self.sets.data[reg]["tech_residual_cap"].loc[:, key]
                )

                (
                    cost_fix_regional[key],
                    cost_fix_tax_regional[key],
                    cost_fix_Sub_regional[key],
                ) = fixcosts(
                    self.sets.data[reg]["tech_fixed_cost"][key],
                    totalcapacity_regional[key],
                    self.sets.data[reg]["fix_taxsub"]["Tax"][key],
                    self.sets.data[reg]["fix_taxsub"]["Sub"][key],
                )

                decomcapacity_regional[key] = decomcap(
                    self.variables["newcapacity"][reg][key],
                    self.sets.Technologies[reg][key],
                    self.sets.main_years,
                    self.sets.data[reg]["tech_lifetime"].loc[:, key],
                )

                cost_decom_regional[key] = cp.multiply(
                    self.sets.data[reg]["tech_decom_cost"].loc[:, key].values,
                    decomcapacity_regional[key],
                )

                production_annual_regional[key] = annual_activity(
                    self.variables["productionbyTechnology"][reg][key],
                    self.sets.main_years,
                    self.sets.time_steps,
                )

                cost_variable_regional[key] = cp.multiply(
                    production_annual_regional[key],
                    self.sets.data[reg]["tech_var_cost"].loc[:, key],
                )

                if key != "Transmission" and key != "Storage":

                    CO2_equivalent_regional[key] = cp.multiply(
                        production_annual_regional[key],
                        self.sets.data[reg]["specific_emission"].loc[:, key],
                    )

                    emission_cost_regional[key] = cp.multiply(
                        CO2_equivalent_regional[key],
                        self.sets.data[reg]["carbon_tax"].loc[:, key],
                    )

                cost_fvalue_regional[key] = invcosts_annuity(
                    cost_inv_regional[key],
                    self.sets.data[reg]["interest_rate"].loc[:, key],
                    self.sets.data[reg]["economic_lifetime"].loc[:, key],
                    self.sets.Technologies[reg][key],
                    self.sets.main_years,
                    self.sets.data[reg]["discount_rate"],
                )

            self.cost_inv[reg] = cost_inv_regional
            self.cost_inv_tax[reg] = cost_inv_tax_regional
            self.cost_inv_sub[reg] = cost_inv_sub_regional
            self.salvage_inv[reg] = salvage_inv_regional
            self.totalcapacity[reg] = totalcapacity_regional
            self.cost_fix[reg] = cost_fix_regional
            self.cost_fix_tax[reg] = cost_fix_tax_regional
            self.cost_fix_sub[reg] = cost_fix_Sub_regional
            self.decommissioned_capacity[reg] = decomcapacity_regional
            self.cost_decom[reg] = cost_decom_regional
            self.cost_variable[reg] = cost_variable_regional
            self.CO2_equivalent[reg] = CO2_equivalent_regional
            self.emission_cost[reg] = emission_cost_regional
            self.cost_inv_fvalue[reg] = cost_fvalue_regional
            self.production_annual[reg] = production_annual_regional

    def _calc_variable_planning_line(self):

        """
        Calculates all the cost and intermediate variables related to the inter-
        regional links in the planning mode
        """

        self.cost_inv_line = {}
        self.line_accumulated_newcapacity = {}
        self.line_totalcapacity = {}
        self.cost_fix_line = {}
        self.line_decommissioned_capacity = {}
        self.cost_decom_line = {}

        for key in self.variables["line_newcapacity"].keys():

            self.cost_inv_line[key] = cp.multiply(
                self.sets.trade_data["line_inv"].loc[:, key].values,
                self.variables["line_newcapacity"][key],
            )

            self.line_accumulated_newcapacity[key] = line_newcap_accumulated(
                self.variables["line_newcapacity"][key],
                self.sets.glob_mapping["Carriers_glob"]["Carrier"],
                self.sets.main_years,
                self.sets.trade_data["line_lifetime"].loc[:, key],
            )

            self.line_totalcapacity[key] = (
                self.line_accumulated_newcapacity[key]
                + self.sets.trade_data["line_residual_cap"].loc[:, key].values
            )

            self.cost_fix_line[key] = cp.multiply(
                self.sets.trade_data["line_fixed_cost"].loc[:, key].values,
                self.line_totalcapacity[key],
            )

            self.line_decommissioned_capacity[key] = line_decomcap(
                self.variables["line_newcapacity"][key],
                self.sets.glob_mapping["Carriers_glob"]["Carrier"],
                self.sets.main_years,
                self.sets.trade_data["line_lifetime"].loc[:, key],
            )

            self.cost_decom_line[key] = cp.multiply(
                self.sets.trade_data["line_decom_cost"].loc[:, key].values,
                self.line_decommissioned_capacity[key],
            )

        self.cost_variable_line = line_varcost(
            self.sets.trade_data["line_var_cost"],
            self.variables["line_import"],
            self.sets.regions,
            self.sets.main_years,
            self.sets.time_steps,
            self.sets.lines_list,
        )

    def _calc_variable_operation(self):

        """
        Calculates all the cost components of the objective function and the
        intermediate variables in the operation mode, for each region
        """

        self.totalcapacity = {}
        self.cost_fix = {}
        self.cost_fix_tax = {}
        self.cost_fix_sub = {}
        self.cost_variable = {}
        self.CO2_equivalent = {}
        self.emission_cost = {}
        self.production_annual = {}
        for reg in self.sets.regions:

            totalcapacity_regional = {}
            cost_fix_regional = {}
            cost_fix_tax_regional = {}
            cost_fix_Sub_regional = {}
            cost_variable_regional = {}
            CO2_equivalent_regional = {}
            emission_cost_regional = {}
            production_annual_regional = {}

            for key in self.sets.Technologies[reg].keys():

                if key != "Demand":

                    totalcapacity_regional[key] = (
                        self.sets.data[reg]["tech_residual_cap"].loc[:, key].values
                    )

                    (
                        cost_fix_regional[key],
                        cost_fix_tax_regional[key],
                        cost_fix_Sub_regional[key],
                    ) = fixcosts(
                        self.sets.data[reg]["tech_fixed_cost"][key],
                        totalcapacity_regional[key],
                        self.sets.data[reg]["fix_taxsub"]["Tax"][key],
                        self.sets.data[reg]["fix_taxsub"]["Sub"][key],
                    )

                    production_annual_regional[key] = annual_activity(
                        self.variables["productionbyTechnology"][reg][key],
                        self.sets.main_years,
                        self.sets.time_steps,
                    )

                    cost_variable_regional[key] = cp.multiply(
                        production_annual_regional[key],
                        self.sets.data[reg]["tech_var_cost"].loc[:, key],
                    )

                    if key != "Transmission" and key != "Storage":

                        CO2_equivalent_regional[key] = cp.multiply(
                            production_annual_regional[key],
                            self.sets.data[reg]["specific_emission"].loc[:, key],
                        )

                        emission_cost_regional[key] = cp.multiply(
                            CO2_equivalent_regional[key],
                            self.sets.data[reg]["carbon_tax"].loc[:, key],
                        )

            self.totalcapacity[reg] = totalcapacity_regional
            self.cost_fix[reg] = cost_fix_regional
            self.cost_fix_tax[reg] = cost_fix_tax_regional
            self.cost_fix_sub[reg] = cost_fix_Sub_regional
            self.cost_variable[reg] = cost_variable_regional
            self.CO2_equivalent[reg] = CO2_equivalent_regional
            self.emission_cost[reg] = emission_cost_regional
            self.production_annual[reg] = production_annual_regional

    def _calc_variable_operation_line(self):

        """
        Calculates all the cost and intermediate variables related to the inter-
        regional links in the operation mode
        """

        self.line_totalcapacity = {}
        self.cost_fix_line = {}
        for key in self.sets.lines_list:

            self.line_totalcapacity[key] = (
                self.sets.trade_data["line_residual_cap"].loc[:, key].values
            )
            self.cost_fix_line[key] = cp.multiply(
                self.sets.trade_data["line_fixed_cost"].loc[:, key].values,
                self.line_totalcapacity[key],
            )

        self.cost_variable_line = line_varcost(
            self.sets.trade_data["line_var_cost"],
            self.variables["line_import"],
            self.sets.regions,
            self.sets.main_years,
            self.sets.time_steps,
            self.sets.lines_list,
        )

    def _calc_variable_storage_SOC(self):

        """
        Calculates the annual state of charge of the on grid storage technologies,
        in the models with hourly temporal resolution
        """

        self.storage_SOC = {}

        for reg in get_regions_with_storage(self.sets):

            self.storage_SOC[reg] = storage_state_of_charge(
                self.sets.data[reg]["storage_initial_SOC"],
                self.variables["usebyTechnology"][reg]["Storage"],
                self.variables["productionbyTechnology"][reg]["Storage"],
                self.sets.main_years,
                self.sets.time_steps,
                self.sets.data[reg]["storage_charge_efficiency"],
                self.sets.data[reg]["storage_discharge_efficiency"],
            )

    def _balance_(self):

        """
        Creates the dictionaries for the annual total production by each technology,
        total consumption by each technology, total import,total exports and total final demand
        of each energy carrier within each region
        """

        self.totalusebycarrier = {}
        self.totalprodbycarrier = {}
        self.totalimportbycarrier = {}
        self.totalexportbycarrier = {}
        self.totaldemandbycarrier = {}

        for reg in self.sets.regions:

            totalusebycarrier_regional = {}
            totalprodbycarrier_regional = {}
            totalimportbycarrier_regional = {}
            totalexportbycarrier_regional = {}
            totaldemandbycarrier_regional = {}

            for carr in self.sets.glob_mapping["Carriers_glob"]["Carrier"]:

                totalusebycarrier_regional[carr] = np.zeros(
                    (len(self.sets.main_years) * len(self.sets.time_steps),)
                )
                totalprodbycarrier_regional[carr] = np.zeros(
                    (len(self.sets.main_years) * len(self.sets.time_steps),)
                )
                totalimportbycarrier_regional[carr] = np.zeros(
                    (len(self.sets.main_years) * len(self.sets.time_steps),)
                )
                totalexportbycarrier_regional[carr] = np.zeros(
                    (len(self.sets.main_years) * len(self.sets.time_steps),)
                )
                totaldemandbycarrier_regional[carr] = np.zeros(
                    (len(self.sets.main_years) * len(self.sets.time_steps),)
                )

                for key in self.sets.Technologies[reg].keys():

                    for indx, tech in enumerate(self.sets.Technologies[reg][key]):

                        if (
                            carr
                            in self.sets.mapping[reg]["Carrier_input"]
                            .loc[
                                self.sets.mapping[reg]["Carrier_input"]["Technology"]
                                == tech
                            ]["Carrier_in"]
                            .values
                        ):

                            if key == "Conversion_plus":

                                totalusebycarrier_regional[carr] += cp.multiply(
                                    self.variables["usebyTechnology"][reg][key][
                                        :, indx
                                    ],
                                    self.sets.data[reg]["carrier_ratio_in"][
                                        (tech, carr)
                                    ].values,
                                )

                            elif key == "Demand":

                                totaldemandbycarrier_regional[carr] += self.sets.data[
                                    reg
                                ]["demand"][tech].values

                            elif key != "Supply":

                                totalusebycarrier_regional[carr] += self.variables[
                                    "usebyTechnology"
                                ][reg][key][:, indx]

                        if (
                            carr
                            in self.sets.mapping[reg]["Carrier_output"]
                            .loc[
                                self.sets.mapping[reg]["Carrier_output"]["Technology"]
                                == tech
                            ]["Carrier_out"]
                            .values
                        ):
                            if key == "Conversion_plus":

                                totalprodbycarrier_regional[carr] += cp.multiply(
                                    self.variables["productionbyTechnology"][reg][key][
                                        :, indx
                                    ],
                                    self.sets.data[reg]["carrier_ratio_out"][
                                        (tech, carr)
                                    ].values,
                                )
                            else:

                                totalprodbycarrier_regional[carr] += self.variables[
                                    "productionbyTechnology"
                                ][reg][key][:, indx]

                if len(self.sets.regions) > 1:

                    for key in self.variables["line_import"][reg].keys():

                        if "{}-{}".format(reg, key) in self.sets.lines_list:

                            line_eff = (
                                pd.concat(
                                    [
                                        self.sets.trade_data["line_eff"][
                                            ("{}-{}".format(reg, key), carr)
                                        ]
                                    ]
                                    * len(self.sets.time_steps)
                                )
                                .sort_index()
                                .values
                            )

                        elif "{}-{}".format(key, reg) in self.sets.lines_list:

                            line_eff = (
                                pd.concat(
                                    [
                                        self.sets.trade_data["line_eff"][
                                            ("{}-{}".format(key, reg), carr)
                                        ]
                                    ]
                                    * len(self.sets.time_steps)
                                )
                                .sort_index()
                                .values
                            )

                        totalimportbycarrier_regional[carr] += cp.multiply(
                            self.variables["line_import"][reg][key][
                                :,
                                list(
                                    self.sets.glob_mapping["Carriers_glob"]["Carrier"]
                                ).index(carr),
                            ],
                            line_eff,
                        )

                        totalexportbycarrier_regional[carr] += self.variables[
                            "line_export"
                        ][reg][key][
                            :,
                            list(
                                self.sets.glob_mapping["Carriers_glob"]["Carrier"]
                            ).index(carr),
                        ]

            self.totalusebycarrier[reg] = totalusebycarrier_regional
            self.totalprodbycarrier[reg] = totalprodbycarrier_regional
            self.totalimportbycarrier[reg] = totalimportbycarrier_regional
            self.totalexportbycarrier[reg] = totalexportbycarrier_regional
            self.totaldemandbycarrier[reg] = totaldemandbycarrier_regional

    def _constr_balance(self):

        """
        Ensures the energy balance of each carrier within each region
        """
        for reg in self.sets.regions:
            for carr in self.sets.glob_mapping["Carriers_glob"]["Carrier"]:

                self.totalusebycarrier[reg][carr] = cp.reshape(
                    self.totalusebycarrier[reg][carr],
                    self.totalprodbycarrier[reg][carr].shape,
                )

                self.constr.append(
                    self.totalprodbycarrier[reg][carr]
                    + self.totalimportbycarrier[reg][carr]
                    - self.totalusebycarrier[reg][carr]
                    - self.totalexportbycarrier[reg][carr]
                    - self.totaldemandbycarrier[reg][carr]
                    == 0
                )

    def _constr_trade_balance(self):

        """
        Ensure sthe trade balance among any pairs of regions before the transmission
        loss
        """

        for reg in self.sets.regions:

            for key in self.variables["line_import"][reg].keys():

                self.constr.append(
                    self.variables["line_import"][reg][key]
                    - self.variables["line_export"][key][reg]
                    == 0
                )

    def _constr_resource_tech_availability(self):

        """
        Guarantees the adequecy of total capacity of each technology based on
        the technology capacity factor and resource availability
        """

        for reg in self.sets.regions:

            for key in self.variables["productionbyTechnology"][reg].keys():

                if key != "Storage":

                    for indx, year in enumerate(self.sets.main_years):

                        self.available_prod = available_resource_prod(
                            self.totalcapacity[reg][key][indx : indx + 1, :],
                            self.sets.data[reg]["res_capacity_factor"]
                            .loc[(year, slice(None)), (key, slice(None))]
                            .values,
                            self.timeslice_fraction,
                            self.sets.data[reg]["annualprod_per_unitcapacity"]
                            .loc[:, (key, slice(None))]
                            .values,
                        )

                        self.constr.append(
                            self.available_prod
                            - self.variables["productionbyTechnology"][reg][key][
                                indx
                                * len(self.sets.time_steps) : (indx + 1)
                                * len(self.sets.time_steps),
                                :,
                            ]
                            >= 0
                        )

                        self.constr.append(
                            cp.multiply(
                                cp.sum(self.available_prod, axis=0),
                                self.sets.data[reg]["tech_capacity_factor"].loc[
                                    year, (key, slice(None))
                                ],
                            )
                            - cp.sum(
                                self.variables["productionbyTechnology"][reg][key][
                                    indx
                                    * len(self.sets.time_steps) : (indx + 1)
                                    * len(self.sets.time_steps),
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

        for reg in self.sets.regions:

            for key, value in self.variables["line_import"][reg].items():

                for indx, year in enumerate(self.sets.main_years):

                    if "{}-{}".format(reg, key) in self.sets.lines_list:

                        capacity_factor = (
                            self.sets.trade_data["line_capacity_factor"]
                            .loc[year, ("{}-{}".format(reg, key), slice(None))]
                            .values
                        )
                        capacity_to_production = (
                            self.sets.trade_data["annualprod_per_unitcapacity"]
                            .loc[:, ("{}-{}".format(reg, key), slice(None))]
                            .values
                        )
                        capacity = self.line_totalcapacity["{}-{}".format(reg, key)][
                            indx : indx + 1, :
                        ]

                    elif "{}-{}".format(key, reg) in self.sets.lines_list:

                        capacity_factor = (
                            self.sets.trade_data["line_capacity_factor"]
                            .loc[year, ("{}-{}".format(key, reg), slice(None))]
                            .values
                        )
                        capacity_to_production = (
                            self.sets.trade_data["annualprod_per_unitcapacity"]
                            .loc[:, ("{}-{}".format(key, reg), slice(None))]
                            .values
                        )
                        capacity = self.line_totalcapacity["{}-{}".format(key, reg)][
                            indx : indx + 1, :
                        ]

                    line_import = cp.sum(
                        value[
                            indx
                            * len(self.sets.time_steps) : (indx + 1)
                            * len(self.sets.time_steps),
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
                            * len(self.sets.time_steps) : (indx + 1)
                            * len(self.sets.time_steps),
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
        for reg in self.sets.regions:

            for key, value in self.totalcapacity[reg].items():

                self.constr.append(
                    value - self.sets.data[reg]["tech_mintotcap"].loc[:, key].values
                    >= 0
                )
                self.constr.append(
                    value - self.sets.data[reg]["tech_maxtotcap"].loc[:, key] <= 0
                )

    def _constr_totalcapacity_overall(self):

        """
        Defines the annual upper and lower limit on the aggregated total capacity
        of each technology over all the regions
        """

        self.totalcapacity_overall = _calc_variable_overall(
            self.sets.glob_mapping["Technologies_glob"],
            self.sets.regions,
            self.sets.main_years,
            self.sets.Technologies,
            self.totalcapacity,
        )

        for tech, value in self.totalcapacity_overall.items():

            self.constr.append(
                value - self.sets.global_data["global_mintotcap"].loc[:, tech].values
                >= 0
            )
            self.constr.append(
                value - self.sets.global_data["global_maxtotcap"].loc[:, tech].values
                <= 0
            )

    def _constr_totalcapacity_line(self):

        """
        Defines the upper and lower limit on the annual total capacity of the
        inter-regional links
        """

        for key, value in self.line_totalcapacity.items():

            self.constr.append(
                value <= self.sets.trade_data["line_maxtotcap"][key].values
            )
            self.constr.append(
                value >= self.sets.trade_data["line_mintotcap"][key].values
            )

    def _constr_newcapacity_regional(self):

        """
        Defines the upper and lower limit on the annual new installed capacity
        of each technology within each region
        """

        for reg in self.sets.regions:

            for key, value in self.variables["newcapacity"][reg].items():

                self.constr.append(
                    value >= self.sets.data[reg]["tech_min_newcap"].loc[:, key]
                )
                self.constr.append(
                    value <= self.sets.data[reg]["tech_max_newcap"].loc[:, key]
                )

    def _constr_newcapacity_overall(self):

        """
        Defines the upper and lower limit on the aggregated new installed capacity
        of each technology over all the regions
        """

        self.newcapacity_overall = _calc_variable_overall(
            self.sets.glob_mapping["Technologies_glob"],
            self.sets.regions,
            self.sets.main_years,
            self.sets.Technologies,
            self.variables["newcapacity"],
        )

        for tech, value in self.newcapacity_overall.items():
            self.constr.append(
                value - self.sets.global_data["global_min_newcap"].loc[:, tech] >= 0
            )
            self.constr.append(
                value - self.sets.global_data["global_max_newcap"].loc[:, tech] <= 0
            )

    def _constr_newcapacity_line(self):

        """
        Defines the upper and lower limit on the annual new installed capacity
        of the inter-regional links
        """

        for key, value in self.variables["newcapaciy"].items():

            self.constr.append(value <= self.sets.trade_data["line_max_newcap"][key])
            self.constr.append(value >= self.sets.trade_data["line_min_newcap"][key])

    def _constr_tech_efficiency(self):

        """
        Defines the relationship between the input and output activity of 
        conversion, transmission and conversion-plus technologies
        """

        for reg in self.sets.regions:

            for key, value in self.variables["productionbyTechnology"][reg].items():

                if key != "Supply" and key != "Storage":

                    tech_efficiency_reshape = pd.concat(
                        [self.sets.data[reg]["tech_efficiency"][key]]
                        * len(self.sets.time_steps)
                    ).sort_index()

                    self.constr.append(
                        value
                        - cp.multiply(
                            self.variables["usebyTechnology"][reg][key],
                            tech_efficiency_reshape.values,
                        )
                        == 0
                    )

    def _constr_prod_annual(self):

        """
        Defines the upper and lower limit for the annual production of the technologies
        within each region
        """

        for reg in self.sets.regions:

            for key, value in self.variables["productionbyTechnology"][reg].items():

                production_annual = annual_activity(
                    value, self.sets.main_years, self.sets.time_steps,
                )
                if key != "Transmission" and key != "Storage":

                    self.constr.append(
                        production_annual
                        - self.sets.data[reg]["tech_max_production"].loc[
                            :, (key, slice(None))
                        ]
                        <= 0
                    )
                    self.constr.append(
                        production_annual
                        - self.sets.data[reg]["tech_min_production"].loc[
                            :, (key, slice(None))
                        ]
                        >= 0
                    )

    def _constr_prod(self):

        """
        Defines the upper and lower limit for the hourly production of the technologies
        within each region
        """

        for reg in self.sets.regions:

            for key, value in self.variables["productionbyTechnology"][reg].items():

                if key != "Transmission" and key != "Storage":

                    self.constr.append(
                        value
                        - self.sets.data[reg]["tech_max_production_h"].loc[
                            :, (key, slice(None))
                        ]
                        <= 0
                    )
                    self.constr.append(
                        value
                        - self.sets.data[reg]["tech_min_production_h"].loc[
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
            self.sets.glob_mapping["Technologies_glob"],
            self.sets.regions,
            self.sets.main_years,
            self.sets.Technologies,
            self.production_annual,
        )

        for tech, value in self.production_overall.items():

            self.constr.append(
                value - self.sets.global_data["global_min_production"].loc[:, tech] >= 0
            )
            self.constr.append(
                value - self.sets.global_data["global_max_production"].loc[:, tech] <= 0
            )

    def _constr_emission_cap(self):

        """
        Defines the CO2 emission cap within each region and over all the regions
        """
        self.regional_emission = {}
        self.global_emission = np.zeros(
            (len(self.sets.main_years) * len(self.sets.time_steps), 1)
        )
        for reg in self.sets.regions:

            self.regional_emission[reg] = np.zeros(
                (len(self.sets.main_years) * len(self.sets.time_steps), 1)
            )

            for key, value in self.CO2_equivalent[reg].items():

                self.regional_emission[reg] += cp.sum(value, axis=1)

                emission_cap = self.sets.data[reg]["emission_cap_annual"].values

                emission_cap.shape = self.regional_emission[reg].shape

            self.global_emission += self.regional_emission[reg]

            self.constr.append(emission_cap - self.regional_emission[reg] >= 0)

        if len(self.sets.regions) > 1:

            global_emission_cap = self.sets.global_data[
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
        for reg in get_regions_with_storage(self.sets):

            for indx, year in enumerate(self.sets.main_years):

                self.constr.append(
                    self.totalcapacity[reg]["Storage"][indx : indx + 1, :]
                    - self.storage_SOC[reg][
                        indx
                        * len(self.sets.time_steps) : (indx + 1)
                        * len(self.sets.time_steps),
                        :,
                    ]
                    >= 0
                )

                self.constr.append(
                    self.storage_SOC[reg][
                        indx
                        * len(self.sets.time_steps) : (indx + 1)
                        * len(self.sets.time_steps),
                        :,
                    ]
                    - cp.multiply(
                        self.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                        self.sets.data[reg]["storage_min_SOC"].values[
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

        for reg in get_regions_with_storage(self.sets):

            for indx, year in enumerate(self.sets.main_years):

                max_storage_flow_in = storage_max_flow(
                    self.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                    self.sets.data[reg]["storage_charge_time"].values,
                    self.sets.data[reg]["tech_capacity_factor"]["Storage"].values[
                        indx : indx + 1, :
                    ],
                    self.timeslice_fraction,
                )

                max_storage_flow_out = storage_max_flow(
                    self.totalcapacity[reg]["Storage"][indx : indx + 1, :],
                    self.sets.data[reg]["storage_discharge_time"].values,
                    self.sets.data[reg]["tech_capacity_factor"]["Storage"].values[
                        indx : indx + 1, :
                    ],
                    self.timeslice_fraction,
                )

                self.constr.append(
                    max_storage_flow_in
                    - self.variables["usebyTechnology"][reg]["Storage"][
                        indx
                        * len(self.sets.time_steps) : (indx + 1)
                        * len(self.sets.time_steps),
                        :,
                    ]
                    >= 0
                )

                self.constr.append(
                    max_storage_flow_out
                    - self.variables["productionbyTechnology"][reg]["Storage"][
                        indx
                        * len(self.sets.time_steps) : (indx + 1)
                        * len(self.sets.time_steps),
                        :,
                    ]
                    >= 0
                )

    def _set_regional_objective_planning(self):

        """
        Calculates the regional objective function in the planning mode
        """

        self.totalcost_allregions = np.zeros((len(self.sets.main_years), 1))
        self.inv_allregions = 0
        years = -1 * np.arange(len(self.sets.main_years))

        for reg in self.sets.regions:

            totalcost_regional = np.zeros((len(self.sets.main_years), 1))

            for ctgry in self.sets.Technologies[reg].keys():

                if ctgry != "Demand":

                    totalcost_regional += cp.sum(
                        self.cost_inv_tax[reg][ctgry]
                        - self.cost_inv_sub[reg][ctgry]
                        + self.cost_fix[reg][ctgry]
                        + self.cost_fix_tax[reg][ctgry]
                        - self.cost_fix_sub[reg][ctgry]
                        + self.cost_variable[reg][ctgry]
                        + self.cost_decom[reg][ctgry]
                        - self.salvage_inv[reg][ctgry],
                        axis=1,
                    )

                    self.inv_allregions += self.cost_inv_fvalue[reg][ctgry]

                    if ctgry != "Transmission" and ctgry != "Storage":

                        totalcost_regional += cp.sum(
                            self.emission_cost[reg][ctgry], axis=1
                        )

            discount_factor = (
                1 + self.sets.data[reg]["discount_rate"]["Annual Discount Rate"].values
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
        for reg in self.sets.regions:

            totalcost_regional = 0

            for ctgry in self.sets.Technologies[reg].keys():

                if ctgry != "Demand":

                    totalcost_regional += cp.sum(
                        self.cost_fix[reg][ctgry]
                        + self.cost_fix_tax[reg][ctgry]
                        - self.cost_fix_sub[reg][ctgry]
                        + self.cost_variable[reg][ctgry]
                    )

                    if ctgry != "Transmission" and ctgry != "Storage":

                        totalcost_regional += cp.sum(
                            self.emission_cost[reg][ctgry], axis=1
                        )

            self.totalcost_allregions += totalcost_regional

    def _set_lines_objective_planning(self):

        """
        Calculates the objective function of the inter-regional links in the 
        planning mode
        """

        years = -1 * np.arange(len(self.sets.main_years))
        self.totalcost_lines = np.zeros((len(self.sets.main_years), 1))

        for line in self.sets.lines_list:

            self.totalcost_lines += cp.sum(
                self.cost_inv_line[line]
                + self.cost_fix_line[line]
                + self.cost_decom_line[line],
                axis=1,
            )

        for reg in self.sets.regions:

            for key, value in self.cost_variable_line[reg].items():

                self.totalcost_lines += cp.sum(value, axis=1)

        discount_factor_global = (
            1
            + self.sets.global_data["global_discount_rate"][
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

        self.totalcost_lines = np.zeros((len(self.sets.main_years), 1))

        for line in self.sets.lines_list:

            self.totalcost_lines += cp.sum(self.cost_fix_line[line], axis=1)

        for reg in self.sets.regions:

            for key, value in self.cost_variable_line[reg].items():

                self.totalcost_lines += cp.sum(value, axis=1)

    def _set_final_objective_singlenode(self):

        """
        Calculates the overall objective function in a single-node model
        """

        if self.sets.mode == "Planning":

            self.global_objective = (
                cp.sum(self.totalcost_allregions) + self.inv_allregions
            )

        elif self.sets.mode == "Operation":

            self.global_objective = self.totalcost_allregions

    def _set_final_objective_multinode(self):

        """
        Calculates the overall objective function as the summation of all the
        regional and inter-regional links objective functions in a multi-node
        model
        """

        if self.sets.mode == "Planning":

            self.global_objective = (
                cp.sum(self.totalcost_lines_discounted + self.totalcost_allregions)
                + self.inv_allregions
            )

        elif self.sets.mode == "Operation":

            self.global_objective = self.totalcost_allregions + self.totalcost_lines
