import pandas as pd
import unittest
from hypatia.utility.utility import create_technology_columns

'''
Unit tests for the functions in utility.py
'''
class TestCreateTechnologyColumns(unittest.TestCase):
    technologies_hierarchy = {
        "Supply": ["NG_extraction", "Geo_PP"],
        "Conversion": ["Boiler"],
        "Demand": ["Elec_demand", "Heat_demand"],
    }

    def test_create_technology_columns(self):
        expected = pd.MultiIndex.from_arrays(
                [
                    ["Supply", "Supply", "Conversion", "Demand", "Demand"],
                    ["NG_extraction", "Geo_PP", "Boiler", "Elec_demand", "Heat_demand"],
                ],
                names=["Tech_category", "Technology"]
            )

        self.assertTrue(
            expected.equals(
                create_technology_columns(self.technologies_hierarchy, ignored_tech_categories=[])
            )
        )

    def test_create_technology_columns_ignore_tech(self):
        # check ignoring demand is the default behavior
        expected = pd.MultiIndex.from_arrays(
                [
                    ["Supply", "Supply", "Conversion"],
                    ["NG_extraction", "Geo_PP", "Boiler"],
                ],
                names=["Tech_category", "Technology"]
            )

        self.assertTrue(
            expected.equals(
                create_technology_columns(self.technologies_hierarchy)
            )
        )


        # check we can ignore multiple technologies
        expected = pd.MultiIndex.from_arrays(
                [
                    ["Supply", "Supply"],
                    ["NG_extraction", "Geo_PP"],
                ],
                names=["Tech_category", "Technology"]
            )

        self.assertTrue(
            expected.equals(
                create_technology_columns(
                    self.technologies_hierarchy,
                    ignored_tech_categories=["Demand", "Conversion"]
                )
            )
        )

    def test_create_technology_columns_add_layer(self):
        # check we can correctly add an additional top layer
        expected = pd.MultiIndex.from_arrays(
                [
                    ["Tax", "Tax", "Tax", "Sub", "Sub", "Sub"],
                    ["Supply", "Supply", "Conversion", "Supply", "Supply", "Conversion"],
                    ["NG_extraction", "Geo_PP", "Boiler", "NG_extraction", "Geo_PP", "Boiler"],
                ],
                names=["Taxes or Subsidies", "Tech_category", "Technology"]
            )

        self.assertTrue(
            expected.equals(
                create_technology_columns(
                    self.technologies_hierarchy,
                    additional_level=("Taxes or Subsidies", ["Tax", "Sub"])
                )
            )
        )


if __name__ == '__main__':
    unittest.main()
