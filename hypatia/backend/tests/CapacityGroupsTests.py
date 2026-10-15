import unittest
from types import SimpleNamespace

import cvxpy as cp
import numpy as np
import pandas as pd

from hypatia.backend.constraints._capacity_groups import capacity_by_group
from hypatia.backend.constraints.NewCapacityGroup import NewCapacityGroup
from hypatia.backend.constraints.TotalCapacityGroup import TotalCapacityGroup

'''
Unit tests for the capacity group constraints on a small synthetic system:
two regions, three years, technology "PV" present in both regions.
'''

YEARS = ["Y0", "Y1", "Y2"]


def make_case():
    settings = SimpleNamespace(
        years=YEARS,
        regions=["reg1", "reg2"],
        multi_node=False,
        technologies={
            "reg1": {"Supply": ["GAS"], "Conversion": ["PV", "WIND"]},
            "reg2": {"Conversion": ["PV"]},
        },
    )
    totalcapacity = {
        "reg1": {"Supply": cp.Variable((3, 1)), "Conversion": cp.Variable((3, 2))},
        "reg2": {"Conversion": cp.Variable((3, 1))},
    }
    values = {
        ("reg1", "Supply"): [[1.0], [2.0], [3.0]],
        ("reg1", "Conversion"): [[10.0, 100.0], [20.0, 200.0], [30.0, 300.0]],
        ("reg2", "Conversion"): [[5.0], [6.0], [7.0]],
    }
    for (reg, cat), v in values.items():
        totalcapacity[reg][cat].value = np.array(v)
    return settings, totalcapacity


class TestCapacityGroups(unittest.TestCase):

    def test_sum_over_technologies_and_regions(self):
        settings, cap = make_case()
        membership = pd.DataFrame([("RES", "PV"), ("RES", "WIND")], columns=["Group", "Technology"])
        grouped = capacity_by_group(settings, cap, membership)
        # PV in reg1 + WIND in reg1 + PV in reg2
        np.testing.assert_allclose(grouped["RES"].value, [115.0, 226.0, 337.0])
        self.assertEqual(grouped["RES"].shape, (3,))

    def test_group_of_technology_present_nowhere_is_zero(self):
        settings, cap = make_case()
        membership = pd.DataFrame([("NUC", "SMR")], columns=["Group", "Technology"])
        grouped = capacity_by_group(settings, cap, membership)
        np.testing.assert_allclose(grouped["NUC"].value, [0.0, 0.0, 0.0])

    def test_constraint_rows_and_residuals(self):
        settings, cap = make_case()
        membership = pd.DataFrame([("RES", "PV"), ("RES", "WIND")], columns=["Group", "Technology"])
        limits = pd.DataFrame([("RES", y, 200.0) for y in YEARS], columns=["Group", "Year", "Max_totalcap"])
        data = SimpleNamespace(
            settings=settings,
            regional_parameters={"reg1": {"capacity_group_membership": membership,
                                          "group_maxtotcap": limits}},
        )
        rules = TotalCapacityGroup(data, SimpleNamespace(totalcapacity=cap)).rules()
        self.assertEqual(len(rules), 1)
        # cvxpy stores "lhs <= rhs" as lhs - rhs
        np.testing.assert_allclose(rules[0].expr.value, [-85.0, 26.0, 137.0])

    def test_no_sheets_means_no_constraints(self):
        settings, cap = make_case()
        data = SimpleNamespace(settings=settings, regional_parameters={"reg1": {}})
        variables = SimpleNamespace(totalcapacity=cap, real_new_capacity=cap)
        self.assertEqual(TotalCapacityGroup(data, variables).rules(), [])
        self.assertEqual(NewCapacityGroup(data, variables).rules(), [])

    def test_empty_limit_sheet_means_no_constraints(self):
        settings, cap = make_case()
        membership = pd.DataFrame(columns=["Group", "Technology"])
        limits = pd.DataFrame(columns=["Group", "Year", "Max_newcap"])
        data = SimpleNamespace(
            settings=settings,
            regional_parameters={"reg1": {"capacity_group_membership": membership,
                                          "group_max_newcap": limits}},
        )
        variables = SimpleNamespace(real_new_capacity=cap)
        self.assertEqual(NewCapacityGroup(data, variables).rules(), [])


if __name__ == "__main__":
    unittest.main()
