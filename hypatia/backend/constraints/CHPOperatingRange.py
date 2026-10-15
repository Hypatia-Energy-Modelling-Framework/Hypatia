# -*- coding: utf-8 -*-
"""
Variable operating range for CHP plants (feasible operating region).

Original implementation: Tommaso Zacconi, 2025.

Each CHP plant is modelled with three conversion technologies: the CHP unit,
its power branch and its heat branch. For every CHP group listed in the sheet
"CHP_variable_techs_selection" and every region where the three technologies
exist, two constraints are added at every time step:

    heat <= gamma * chp                                  (max heat/power coefficient)
    heat * (eta_e / gamma - eta_e / eta_th) <= power     (power-to-heat ratio)

where eta_e and eta_th are the efficiencies of the power and heat branches,
averaged over the model years.

The number of CHP groups is the number of rows in the sheet. Rows whose names
do not match the conversion technologies of a region (e.g. rows of zeros) are
skipped for that region.
"""

from hypatia.backend.constraints.Constraint import Constraint
from hypatia.utility.utility import (
    get_parameters_from_global_or_regional_file
)

import pandas as pd
import numpy as np
import cvxpy as cp


class CHPOperatingRange(Constraint):

    # Columns of the input sheet, in this order.
    CHP_header_list = ["CHP Tech Name",
                       "Power-branch Tech Name",
                       "Heat-branch Tech Name",
                       "Max Heat Power Coefficient"]

    # Rows written in a new (empty) parameter file. Users can add or remove
    # rows: the constraint uses the rows found in the data.
    DEFAULT_CHP_GROUPS = [1, 2, 3, 4, 5]

    def _check(self):
        assert hasattr(self.variables, 'technology_prod'), "technology_prod must be defined"

    def rules(self):
        rules = []

        # Global file for multi-region models, regional file otherwise.
        CHP_address = get_parameters_from_global_or_regional_file(
            self.model_data.settings,
            self.model_data,
            "glob_variable_CHP_tech_selection",
            "variable_CHP_tech_selection"
        )

        for reg in self.model_data.settings.regions:
            # A region without conversion technologies has no CHP to constrain.
            reg_conv_techs = list(self.model_data.settings.technologies[reg].get("Conversion", []))
            if not reg_conv_techs:
                continue
            prod = self.variables.technology_prod[reg]["Conversion"]

            for row in CHP_address.index:
                name_chp, name_power, name_heat, gamma = CHP_address.loc[row].iloc[:4]

                if not all(name in reg_conv_techs for name in (name_chp, name_power, name_heat)):
                    continue
                i_chp = reg_conv_techs.index(name_chp)
                i_power = reg_conv_techs.index(name_power)
                i_heat = reg_conv_techs.index(name_heat)

                eta_e, eta_th = self._mean_efficiencies(reg, name_power, name_heat, row)
                powerLoss_ratio = eta_e / eta_th
                power2heat_ratio = eta_e / gamma - powerLoss_ratio

                # tech_prod_Heat <= gamma * tech_prod_CHP
                rules.append(prod[:, i_heat] - cp.multiply(prod[:, i_chp], gamma) <= 0)

                # tech_prod_Heat * power2heat_ratio <= tech_prod_Power
                rules.append(cp.multiply(prod[:, i_heat], power2heat_ratio) - prod[:, i_power] <= 0)

        return rules

    def _mean_efficiencies(self, reg, name_power, name_heat, row):
        """Efficiencies of the power and heat branches, averaged over the model years.

        Fails with a clear message instead of returning NaN: NaN coefficients
        would only surface later as a solver error, or not at all.
        """
        try:
            tech_eff_conversion = self.model_data.regional_parameters[reg]["tech_efficiency"]["Conversion"]
            eta_e = float(np.mean(tech_eff_conversion[name_power].values))
            eta_th = float(np.mean(tech_eff_conversion[name_heat].values))
        except KeyError as err:
            raise ValueError(
                f"CHP group {row} in region {reg}: efficiency of '{name_power}' or "
                f"'{name_heat}' not found in the Tech_efficiency sheet ({err})."
            ) from err
        if not (np.isfinite(eta_e) and np.isfinite(eta_th)) or eta_th == 0:
            raise ValueError(
                f"CHP group {row} in region {reg}: invalid efficiencies "
                f"(power branch {eta_e}, heat branch {eta_th})."
            )
        return eta_e, eta_th

    @staticmethod
    def _template():
        return {
            "sheet_name": "CHP_variable_techs_selection",
            "value": 0,
            "index": pd.Index(CHPOperatingRange.DEFAULT_CHP_GROUPS, name="CHP group"),
            "columns": pd.Index(CHPOperatingRange.CHP_header_list),
            # Rows are user-defined: ModelData checks only the columns.
            "variable_index": True,
        }

    def _required_regional_parameters(settings):
        if settings.multi_node:
            return {}
        return {reg: {"variable_CHP_tech_selection": CHPOperatingRange._template()}
                for reg in settings.regions}

    def _required_global_parameters(settings):
        # Same key that rules() reads for multi-region models.
        return {"glob_variable_CHP_tech_selection": CHPOperatingRange._template()}
