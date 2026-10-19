import unittest

import cvxpy as cp
import numpy as np

from hypatia.backend.constraints._terms import is_power_carrier, sum_terms

'''
Unit tests for the helpers in constraints/_terms.py
'''


class TestTerms(unittest.TestCase):

    def test_power_carrier_names(self):
        for name in ["Electricity", "electricity", " Electricity ", "POWER", "power"]:
            self.assertTrue(is_power_carrier(name), name)
        # Final electricity is a demand-side carrier, not production.
        for name in ["Final_electricity", "Heat", "Electricity_HV", None]:
            self.assertFalse(is_power_carrier(name), name)

    def test_empty_sum(self):
        self.assertIsNone(sum_terms([]))
        zero = sum_terms([], zero_shape=(3, 1))
        self.assertEqual(zero.shape, (3, 1))
        np.testing.assert_array_equal(zero.value, np.zeros((3, 1)))

    def test_sum_value(self):
        x = cp.Variable(3)
        y = cp.Variable(3)
        x.value = np.array([1.0, 2.0, 3.0])
        y.value = np.array([10.0, 20.0, 30.0])
        np.testing.assert_array_equal(sum_terms([x, y, x]).value, [12.0, 24.0, 36.0])

    def test_sum_does_not_modify_terms(self):
        # The first term must not be changed in place: recent cvxpy forbids it,
        # and it would also silently alter an expression used elsewhere.
        x = cp.Variable(2)
        first = 2 * x
        sum_terms([first, x])
        x.value = np.array([1.0, 1.0])
        np.testing.assert_array_equal(first.value, [2.0, 2.0])

    def test_accepts_generators(self):
        x = cp.Variable(2)
        x.value = np.array([1.0, 2.0])
        np.testing.assert_array_equal(sum_terms(x for _ in range(3)).value, [3.0, 6.0])


if __name__ == "__main__":
    unittest.main()
