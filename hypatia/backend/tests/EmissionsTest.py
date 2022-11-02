import pandas as pd
import numpy as np
import unittest
import copy
from hypatia.backend.ModelSettings import ModelSettings
from hypatia.backend.ModelData import ModelData
from hypatia.utility.constants import ModelMode
from hypatia.backend.Build import BuildModel
from hypatia.backend.tests.TestSettings import (
    SingleNodeOperationEmissionTestSettings,
    SingleNodePlanningEmissionTestSettings,
    MultiNodeOperationEmissionTestSettings,
    MultiNodePlanningEmissionTestSettings
)
import hypatia.error_log.Exceptions as hypatiaException

'''
Test how hypatia models emissions by checking that:
    1. The model correctly tracks the emission generate by the model solution
    2. The model correctly considers emission cost to find the optimal solution
    3. The model correctly considers emission caps (global and regional) to find the optimal solution
We check these feature in the 4 main scenarios:
    1. Single region, planning
    2. Single region, operation
    3. Multi region, planning
    4. Multi region, operation
'''

class TestEmissionsSingleRegionOperation(unittest.TestCase):
    '''
    The scenario used in the test is:

        ------------------------------ Reg1 --------------------------------
        Elec_import                                  -> Elec |
                                                             |-> Elec Demand
                                                    |-> Elec |
        NG_extr -> NG -> NG_ref -> NG_prod -> NG_chp|
                                                    |-> Heat |
                                                             |-> Heat Demand
        Heat_import                                  -> Heat |
    '''

    def __init__(self, *args, **kwargs):
        super(TestEmissionsSingleRegionOperation, self).__init__(*args, **kwargs)

    # Checks the model correctly tracks the emission generate by the model solution
    def test_emission_tracking(self):
        example_settings = SingleNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )

        regional_parameters = settings.default_regional_parameters

        # Increment demand for heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs
        regional_parameters["reg1"]["tech_residual_cap"] += 8760

        # Increment the cost for Heat_import and Elec_import so it is better to fulfil the demand using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the Emission production for the NG transformation technologies
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref","NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG to produced heat and elec and did not import them
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

        # Check how many emission were produced
        expected = np.array([[0.0, 0.0, 0.0]])
        self.assertTrue(np.array_equal(expected, results.emission_by_type["CO2"]["reg1"]["Supply"].value))
        self.assertTrue(np.array_equal(expected, results.emission_by_type["NOx"]["reg1"]["Supply"].value))
        self.assertEqual(
            results.emission_by_type["CO2"]["reg1"]["Conversion"].value,
            [[8760]]
        )
        self.assertEqual(
            results.emission_by_type["CO2"]["reg1"]["Conversion_plus"].value,
            [[8760]]
        )
        self.assertEqual(
            results.emission_by_type["NOx"]["reg1"]["Conversion"].value,
            [[0]]
        )
        self.assertEqual(
            results.emission_by_type["NOx"]["reg1"]["Conversion_plus"].value,
            [[17520]]
        )
        

    # Checks the model correctly considers emission cost to find the optimal solution
    def test_emission_cost_function(self):
        example_settings = SingleNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )

        regional_parameters = settings.default_regional_parameters

        # Increment demand for heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs
        regional_parameters["reg1"]["tech_residual_cap"] += 8760

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the Emission production for the NG transformation technologies
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref","NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG to produced heat and elec and did not import them
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

        # Now increase the emission taxes and show that decide to import heat and elect
        # if the emission taxes makes it more expensive to generate them using NG
        regional_parameters["reg1"]["emission_tax"] += 1
        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we did not import heat and elec and produced them using NG
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10)
        ))

    # Checks the model correctly considers regional emission caps to find the optimal solution
    def test_emission_cap(self):
        example_settings = SingleNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )

        regional_parameters = settings.default_regional_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs in the NG value chain
        regional_parameters["reg1"]["tech_residual_cap"] += 8760

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref","NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG to produced heat and elec and did not import them
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

        # Now introduce an emission cap equal to 0 and show that we pick to import heat and elec
        # even if they are more expensive
        regional_parameters["reg1"]["emission_cap_annual"].values[:] = 0

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we did not import heat and elec and produced them using NG
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10)
        ))
        


class TestEmissionsSingleRegionPlanning(unittest.TestCase):
    '''
    The scenario used in the test is:

    Reg1
        Elec_import                                  -> Elec |
                                                              |-> Elec Demand
                                                    |-> Elec |
        NG_extr -> NG -> NG_ref -> NG_prod -> NG_chp|
                                                    |-> Heat |
                                                              |-> Heat Demand
        Heat_import                                  -> Heat |
    '''

    def __init__(self, *args, **kwargs):
        super(TestEmissionsSingleRegionPlanning, self).__init__(*args, **kwargs)

    # Checks the model correctly tracks the emission generate by the model solution
    def test_emission_tracking(self):
        example_settings = SingleNodePlanningEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )

        regional_parameters = settings.default_regional_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref","NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG to produced heat and elec and did not import them
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

        # # Check how many emission were produced
        expected = np.array([[0.0, 0.0, 0.0]] * len(settings.years))
        self.assertTrue(
            np.array_equal(
                np.array([[0.0, 0.0, 0.0]] * len(settings.years)),
                results.emission_by_type["CO2"]["reg1"]["Supply"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[0.0, 0.0, 0.0]] * len(settings.years)),
                results.emission_by_type["NOx"]["reg1"]["Supply"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[1]] * len(settings.years)),
                results.emission_by_type["CO2"]["reg1"]["Conversion"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[0]] * len(settings.years)),
                results.emission_by_type["NOx"]["reg1"]["Conversion"].value,
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[1]] * len(settings.years)),
                results.emission_by_type["CO2"]["reg1"]["Conversion_plus"].value,
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[2]] * len(settings.years)),
                results.emission_by_type["NOx"]["reg1"]["Conversion_plus"].value,
            )
        )

    # Checks the model correctly considers emission cost to find the optimal solution
    def test_emission_cost_function(self):
        example_settings = SingleNodePlanningEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )

        regional_parameters = settings.default_regional_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref","NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG to produced heat and elec and did not import them
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

        # Now increase the emission taxes and show that decide to import heat and elect
        # if the emission taxes makes it more expensive to generate them using NG
        regional_parameters["reg1"]["emission_tax"] += 1
        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that imported heat and elec and did not produced them using NG
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

    # Checks the model correctly considers regional emission caps to find the optimal solution
    def test_emission_cap(self):
        example_settings = SingleNodePlanningEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )

        regional_parameters = settings.default_regional_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref","NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG to produced heat and elec and did not import them
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

        # Now introduce an emission cap equal to 0 and show that we pick to import heat and elec
        # even if they are more expensive
        regional_parameters["reg1"]["emission_cap_annual"].values[:] = 0
        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that imported heat and elec and did not produced them using NG
        suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["NG_extr"].values, decimals=10)
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(suppy_technology_use["Heat_import"].values, decimals=10),
        ))

class TestEmissionsMultiRegionOperation(unittest.TestCase):
    '''
    The scenario used in the test is:

        --------- Reg1 ---------           ---------------- reg2 -----------------
                                              Elec_import-> Elec |
                                                                  |-> Elec Demand
                                                    |    -> Elec |
        NG_extr -> NG -> NG_ref -> NG_prod -> NG_chp|
                                                    |    -> Heat |
                                                                  |-> Heat Demand
                                              Heat_import-> Heat |
    '''

    def __init__(self, *args, **kwargs):
        super(TestEmissionsMultiRegionOperation, self).__init__(*args, **kwargs)

    # Checks the model correctly tracks the emission generate by the model solution
    def test_emission_tracking(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs in the NG value chain
        regional_parameters["reg1"]["tech_residual_cap"] += 8760
        regional_parameters["reg2"]["tech_residual_cap"] += 8760

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        # Set a line capacity
        trade_parameters["line_residual_cap"].loc[:, (slice(None), ["NG_prod"])] = 8760

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Check how many emission were produced
        self.assertTrue(
            np.array_equal(
                np.array([[8760]]),
                results.emission_by_type["CO2"]["reg1"]["Conversion_plus"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[17520]]),
                results.emission_by_type["NOx"]["reg1"]["Conversion_plus"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[8760]]),
                results.emission_by_type["CO2"]["reg2"]["Conversion"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[0]]),
                results.emission_by_type["NOx"]["reg2"]["Conversion"].value
            )
        )

    # Checks the model correctly considers emission cost to find the optimal solution
    def test_emission_cost_function(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs in the NG value chain
        regional_parameters["reg1"]["tech_residual_cap"] += 8760
        regional_parameters["reg2"]["tech_residual_cap"] += 8760

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        # Set a line capacity
        trade_parameters["line_residual_cap"].loc[:, (slice(None), ["NG_prod"])] = 8760

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Now increase the emission taxes one of the regions and check that now it is better
        # to use the import techs in region 2
        regional_parameters["reg2"]["emission_tax"] += 3
        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

    # Checks the model correctly considers regional emission caps to find the optimal solution
    def test_emission_regional_emission_cap(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs in the NG value chain
        regional_parameters["reg1"]["tech_residual_cap"] += 8760
        regional_parameters["reg2"]["tech_residual_cap"] += 8760

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        # Set a line capacity
        trade_parameters["line_residual_cap"].loc[:, (slice(None), ["NG_prod"])] = 8760

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Now introduce an emission cap equal to 0 and show that we pick to import heat and elec
        # even if they are more expensive
        regional_parameters["reg2"]["emission_cap_annual"].values[:] = 0
        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

    # Checks the model correctly considers global emission caps to find the optimal solution
    def test_emission_global_emission_cap(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs in the NG value chain
        regional_parameters["reg1"]["tech_residual_cap"] += 8760
        regional_parameters["reg2"]["tech_residual_cap"] += 8760

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        # Set a line capacity
        trade_parameters["line_residual_cap"].loc[:, (slice(None), ["NG_prod"])] = 8760

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Now introduce an emission cap equal to 0 and show that we pick to import heat and elec
        # even if they are more expensive
        global_parameters["global_emission_cap_annual"].values[:] = 0
        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

class TestEmissionsMultiRegionPlanning(unittest.TestCase):
    '''
    The scenario used in the test is:

        --------- Reg1 ---------             -------------- reg2 -----------------
                                              Elec_import-> Elec |
                                                                  |-> Elec Demand
                                                    |    -> Elec |
        NG_extr -> NG -> NG_ref -> NG_prod -> NG_chp|
                                                    |    -> Heat |
                                                                  |-> Heat Demand
                                              Heat_import-> Heat |
    '''

    def __init__(self, *args, **kwargs):
        super(TestEmissionsMultiRegionPlanning, self).__init__(*args, **kwargs)

    # Checks the model correctly tracks the emission generate by the model solution
    def test_emission_tracking(self):
        example_settings = MultiNodePlanningEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Check how many emission were produced
        self.assertTrue(
            np.array_equal(
                np.array([[1]] * len(settings.years)),
                results.emission_by_type["CO2"]["reg1"]["Conversion_plus"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[2]] * len(settings.years)),
                results.emission_by_type["NOx"]["reg1"]["Conversion_plus"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[1]] * len(settings.years)),
                results.emission_by_type["CO2"]["reg2"]["Conversion"].value
            )
        )
        self.assertTrue(
            np.array_equal(
                np.array([[0]] * len(settings.years)),
                results.emission_by_type["NOx"]["reg2"]["Conversion"].value
            )
        )

    # Checks the model correctly considers emission cost to find the optimal solution
    def test_emission_cost_function(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Now increase the emission taxes one of the regions and check that now it is better
        # to use the import techs in region 2
        regional_parameters["reg2"]["emission_tax"] += 3
        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

    # Checks the model correctly considers regional emission caps to find the optimal solution
    def test_emission_regional_emission_cap(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Now introduce an emission cap equal to 0 and show that we pick to import heat and elec
        # even if they are more expensive
        regional_parameters["reg2"]["emission_cap_annual"].values[:] = 0
        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

    # Checks the model correctly considers global emission caps to find the optimal solution
    def test_emission_global_emission_cap(self):
        example_settings = MultiNodeOperationEmissionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )
        global_parameters = settings.default_global_parameters
        regional_parameters = settings.default_regional_parameters
        trade_parameters = settings.default_trade_parameters

        # Increment demand of heat and elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for importing heat and elec so it is better to produce them using NG
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import", "Heat_import"])] += 1

        # Increment the emission production per tech
        regional_parameters["reg1"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_chp"])] += 1
        regional_parameters["reg1"]["specific_emission"].loc[:,(["NOx"], slice(None), ["NG_chp"])] += 2
        regional_parameters["reg2"]["specific_emission"].loc[:,(["CO2"], slice(None), ["NG_ref"])] += 1

        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used NG from reg2 and did not use the imports techs in reg1
        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))

        # Now introduce an emission cap equal to 0 and show that we pick to import heat and elec
        # even if they are more expensive
        global_parameters["global_emission_cap_annual"].values[:] = 0
        model_data = ModelData(
            settings,
            global_parameters,
            trade_parameters,
            regional_parameters
        )
        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        reg1_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Elec_import"].values, decimals=10),
        ))
        self.assertTrue(np.array_equal(
            np.ones(len(settings.years) * len(settings.time_steps)),
            np.around(reg1_suppy_technology_use["Heat_import"].values, decimals=10),
        ))
        reg2_suppy_technology_use = pd.DataFrame(
            data=results.technology_prod["reg2"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg2"]["Supply"],
        )
        self.assertTrue(np.array_equal(
            np.zeros(len(settings.years) * len(settings.time_steps)),
            np.around(reg2_suppy_technology_use["NG_extr"].values, decimals=10),
        ))
