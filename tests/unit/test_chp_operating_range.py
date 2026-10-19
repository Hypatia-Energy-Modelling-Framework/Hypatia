import unittest
from types import SimpleNamespace

import cvxpy as cp
import numpy as np
import pandas as pd

from hypatia.backend.constraints.CHPOperatingRange import CHPOperatingRange

'''
Unit tests for CHPOperatingRange on a small synthetic system: 4 time steps,
two regions, the CHP plant (CHP, CHP_P, CHP_H) exists only in reg1.
'''

T = 4
HEADER = CHPOperatingRange.CHP_header_list


def selection(rows):
    """CHP selection table with the given rows and index 1..n."""
    df = pd.DataFrame(rows, columns=HEADER)
    df.index = pd.Index(range(1, len(rows) + 1), name="CHP group")
    return df


def make_case(table, multi_node=True, eta_e=0.4, eta_th=0.8):
    techs = {
        "reg1": {"Conversion": ["BOILER", "CHP", "CHP_P", "CHP_H"]},
        "reg2": {"Conversion": ["BOILER"]},
    }
    if not multi_node:  # a single-region model has one region
        techs = {"reg1": techs["reg1"]}
    settings = SimpleNamespace(regions=list(techs), multi_node=multi_node, technologies=techs)
    eff = {
        "reg1": pd.DataFrame({"BOILER": [0.9, 0.9], "CHP": [1.0, 1.0],
                              "CHP_P": [eta_e, eta_e], "CHP_H": [eta_th, eta_th]}),
        "reg2": pd.DataFrame({"BOILER": [0.9, 0.9]}),
    }
    regional = {reg: {"tech_efficiency": {"Conversion": eff[reg]}} for reg in settings.regions}
    if multi_node:
        global_parameters = {"glob_variable_CHP_tech_selection": table}
    else:
        global_parameters = None
        regional["reg1"]["variable_CHP_tech_selection"] = table
    data = SimpleNamespace(settings=settings, global_parameters=global_parameters,
                           regional_parameters=regional)
    prod = {reg: {"Conversion": cp.Variable((T, len(t["Conversion"])))} for reg, t in techs.items()}
    return data, SimpleNamespace(technology_prod=prod)


class TestCHPOperatingRange(unittest.TestCase):

    def test_multi_region_only_where_plant_exists(self):
        data, variables = make_case(selection([["CHP", "CHP_P", "CHP_H", 0.5]]))
        rules = CHPOperatingRange(data, variables).rules()
        self.assertEqual(len(rules), 2)  # two constraints, reg1 only

    def test_residuals_match_formulation(self):
        gamma, eta_e, eta_th = 0.5, 0.4, 0.8
        data, variables = make_case(selection([["CHP", "CHP_P", "CHP_H", gamma]]),
                                    eta_e=eta_e, eta_th=eta_th)
        x = variables.technology_prod["reg1"]["Conversion"]
        x.value = np.random.default_rng(1).random((T, 4))
        chp, power, heat = x.value[:, 1], x.value[:, 2], x.value[:, 3]
        r_gamma, r_ratio = CHPOperatingRange(data, variables).rules()
        np.testing.assert_allclose(r_gamma.expr.value, heat - gamma * chp)
        ratio = eta_e / gamma - eta_e / eta_th
        np.testing.assert_allclose(r_ratio.expr.value, heat * ratio - power)

    def test_number_of_groups_comes_from_data(self):
        empty = [0, 0, 0, 0]
        for n_rows in (1, 3, 7):
            table = selection([["CHP", "CHP_P", "CHP_H", 0.5]] + [empty] * (n_rows - 1))
            data, variables = make_case(table, multi_node=False)
            self.assertEqual(len(CHPOperatingRange(data, variables).rules()), 2, n_rows)

    def test_zero_rows_are_skipped(self):
        data, variables = make_case(selection([[0, 0, 0, 0], [0, 0, 0, 0]]))
        self.assertEqual(CHPOperatingRange(data, variables).rules(), [])

    def test_missing_efficiency_raises(self):
        data, variables = make_case(selection([["CHP", "CHP_P", "CHP_H", 0.5]]))
        del data.regional_parameters["reg1"]["tech_efficiency"]["Conversion"]["CHP_H"]
        with self.assertRaises(ValueError) as ctx:
            CHPOperatingRange(data, variables).rules()
        self.assertIn("CHP_H", str(ctx.exception))

    def test_templates_use_the_keys_rules_read(self):
        settings = SimpleNamespace(regions=["reg1", "reg2"], multi_node=True)
        self.assertIn("glob_variable_CHP_tech_selection",
                      CHPOperatingRange._required_global_parameters(settings))
        self.assertEqual(CHPOperatingRange._required_regional_parameters(settings), {})
        settings.multi_node = False
        regional = CHPOperatingRange._required_regional_parameters(settings)
        self.assertIn("variable_CHP_tech_selection", regional["reg1"])
        self.assertTrue(regional["reg1"]["variable_CHP_tech_selection"]["variable_index"])


if __name__ == "__main__":
    unittest.main()
