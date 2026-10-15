import unittest

from hypatia.backend.constraints.ConstraintList import (
    CORE_CONSTRAINTS,
    OPTIONAL_CONSTRAINTS,
    active_constraints,
    resolve_optional_constraints,
)
from hypatia.backend.constraints.CHPOperatingRange import CHPOperatingRange
from hypatia.backend.constraints.ProductionRamp import ProductionRamp

'''
Unit tests for the optional-constraint registry in ConstraintList.py
'''


class TestOptionalConstraints(unittest.TestCase):

    def test_default_is_core_only(self):
        # No option means exactly the constraints that were always active.
        self.assertEqual(active_constraints(), CORE_CONSTRAINTS)
        self.assertEqual(active_constraints(None), CORE_CONSTRAINTS)
        self.assertEqual(resolve_optional_constraints(), ())

    def test_optional_constraints_are_not_in_core(self):
        for cls in OPTIONAL_CONSTRAINTS.values():
            self.assertNotIn(cls, CORE_CONSTRAINTS)

    def test_enabled_constraint_is_appended_after_core(self):
        active = active_constraints(["chp_operating_range"])
        self.assertEqual(active[:-1], CORE_CONSTRAINTS)
        self.assertIs(active[-1], CHPOperatingRange)

    def test_names_are_case_insensitive_and_trimmed(self):
        self.assertEqual(
            resolve_optional_constraints([" CHP_Operating_Range "]),
            ("chp_operating_range",),
        )

    def test_single_string_is_accepted(self):
        # A bare string must not be split into characters.
        self.assertEqual(
            resolve_optional_constraints("chp_operating_range"),
            ("chp_operating_range",),
        )

    def test_order_and_duplicates_do_not_matter(self):
        a = active_constraints(["production_ramp", "chp_operating_range"])
        b = active_constraints(["chp_operating_range", "production_ramp", "production_ramp"])
        self.assertEqual(a, b)
        self.assertEqual(a[-2:], [CHPOperatingRange, ProductionRamp])

    def test_unknown_name_fails_loudly(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_optional_constraints(["chp_operating_rang"])
        # The message lists the accepted names, to help fix the typo.
        self.assertIn("chp_operating_range", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
