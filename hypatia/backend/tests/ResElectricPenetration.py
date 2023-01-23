import pandas as pd
import numpy as np
import unittest
import copy
from hypatia.backend.ModelSettings import ModelSettings
from hypatia.backend.ModelData import ModelData
from hypatia.utility.constants import ModelMode
from hypatia.backend.Build import BuildModel
from hypatia.backend.tests.TestSettings import (
    SingleNodeOperationResPenetrationTestSettings,
    SingleNodePlanningResPenetrationTestSettingsTestSettings
)
import hypatia.error_log.Exceptions as hypatiaException

'''
Test how energy production can ramp up or down in each timestep according to the maximum and minimum ramping
capacity of each technology. This test is done by checking that:
    1. The model shfits production from one technology to the other in each time step as long as the increase 
       in production by each technology is not higher than what is specified in the max and min ramping parameters of that technology
We check this feature in the 4 main scenarios:
    1. Single region, planning
    2. Single region, operation
    3. Multi region, planning
    4. Multi region, operation
'''

class TestResPenetrationSingleRegionOperation(unittest.TestCase):
    '''
    The scenario used in the test is:

        ------------------------------ Reg1 --------------------------------
        Elec_import   -> Elec |
                              |
        PV_park       -> Elec |-> Elec Demand
                              |
                     |-> Elec |
        CHP          |
                     |-> Heat |
                              |-> Heat Demand
        Heat import  |-> Heat |
    '''

    def __init__(self, *args, **kwargs):
        super(TestResPenetrationSingleRegionOperation, self).__init__(*args, **kwargs)

    # Checks if the model correctly tracks the technology production by the model solution
    def test_electric_penetration(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodeOperationResPenetrationTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Elec_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["PV_park"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Heat_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["CHP"])] += 8760

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["PV_park"])] += 100
        regional_parameters["reg1"]["renewable_tech"].loc[:, (slice(None), ["PV_park"])] += 1
        regional_parameters["reg1"]["renewable_electric_penetration"] += 0.2

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        
        CHP_elec_prod = round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5)
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [4000])
        self.assertEqual(CHP_elec_prod, [4000])
        

    # Checks if the model correctly tracks the technology production share by the model solution
    def test_max_production_share(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodeOperationProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Elec_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["PV_park"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Heat_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["CHP"])] += 8760

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Heat_import"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_max_production_share"].loc[:, (slice(None), ["PV_park"])] -= 0.9
        regional_parameters["reg1"]["Conv_plus_max_production_share"].loc[:, (['CHP'], ["Elec"])] -= 0.9

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        
        CHP_elec_prod = round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5)
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [876])
        self.assertEqual(CHP_elec_prod, [876])
        
    def test_min_production(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodeOperationProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Elec_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["PV_park"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Heat_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["CHP"])] += 8760

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["CHP"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["PV_park"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_min_production"].loc[:, (slice(None), ["PV_park"])] += 4000
        regional_parameters["reg1"]["Conv_plus_min_production"].loc[:, (['CHP'], ["Elec"])] += 4000


        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        
        CHP_elec_prod = round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5)
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [4000])
        self.assertEqual(CHP_elec_prod, [4000])
        
    def test_min_production_share(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodeOperationProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Operation,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the residual capacity for all techs
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Elec_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["PV_park"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["Heat_import"])] += 8760
        regional_parameters["reg1"]["tech_residual_cap"].loc[:, (slice(None), ["CHP"])] += 8760

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["PV_park"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["CHP"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_min_production_share"].loc[:, (slice(None), ["PV_park"])] += 0.1
        regional_parameters["reg1"]["Conv_plus_min_production_share"].loc[:, (['CHP'], ["Elec"])] += 0.1

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        
        CHP_elec_prod = round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5)
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [876])
        self.assertEqual(CHP_elec_prod, [876])
    
class TestProductionSingleRegionPlanning(unittest.TestCase):
    '''
    The scenario used in the test is:

        ------------------------------ Reg1 --------------------------------
        Elec_import   -> Elec |
                              |-> Elec Demand
        PV_park       -> Elec |
        
    '''

    def __init__(self, *args, **kwargs):
        super(TestProductionSingleRegionPlanning, self).__init__(*args, **kwargs)

    # Checks if the model correctly tracks the technology max production by the model solution
    def test_max_production(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodePlanningProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Heat_import"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_max_production"].loc[:, (slice(None), ["PV_park"])] -= 1e20
        regional_parameters["reg1"]["tech_max_production"].loc[:, (slice(None), ["PV_park"])] += 4000
        regional_parameters["reg1"]["Conv_plus_max_production"].loc[:, (['CHP'], ["Elec"])] -= 1e20
        regional_parameters["reg1"]["Conv_plus_max_production"].loc[:, (['CHP'], ["Elec"])] += 4000


        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [12000])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][0:8760].values),5), [4000])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][8760:17520].values),5), [4000])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][17520:26280].values),5), [4000])
        
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5), [12000])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][0:8760].values)*0.6 , 5), [4000])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][8760:17520].values)*0.6 , 5), [4000])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][17520:26280].values)*0.6 , 5), [4000])
        
        
    def test_max_production_share(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodePlanningProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Elec_import"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["Heat_import"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_max_production_share"].loc[:, (slice(None), ["PV_park"])] -= 0.9
        regional_parameters["reg1"]["Conv_plus_max_production_share"].loc[:, (['CHP'], ["Elec"])] -= 0.9

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [2628])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][0:8760].values),5), [876])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][8760:17520].values),5), [876])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][17520:26280].values),5), [876])
        
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5), [2628])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][0:8760].values)*0.6 , 5), [876])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][8760:17520].values)*0.6 , 5), [876])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][17520:26280].values)*0.6 , 5), [876])
        
    # Checks if the model correctly tracks the technology min production by the model solution
    def test_min_production(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodePlanningProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["PV_park"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["CHP"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_min_production"].loc[:, (slice(None), ["PV_park"])] += 4000
        regional_parameters["reg1"]["Conv_plus_min_production"].loc[:, (['CHP'], ["Elec"])] += 4000


        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [12000])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][0:8760].values),5), [4000])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][8760:17520].values),5), [4000])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][17520:26280].values),5), [4000])
        
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5), [12000])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][0:8760].values)*0.6 , 5), [4000])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][8760:17520].values)*0.6 , 5), [4000])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][17520:26280].values)*0.6 , 5), [4000])
        
        
    def test_min_production_share(self):
        
        # load the sets from TestSettings.py
        example_settings = SingleNodePlanningProductionTestSettings()
        settings = ModelSettings(
            ModelMode.Planning,
            example_settings.global_settings,
            example_settings.regional_settings,
        )


        # define the numerical parameters
        regional_parameters = settings.default_regional_parameters

        # Increment demand for elec to 1 for each timestamp
        regional_parameters["reg1"]["demand"] += 1

        # Increment the cost for Elec_import so it is better to fulfil the demand using PV park
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["PV_park"])] += 100
        regional_parameters["reg1"]["tech_var_cost"].loc[:, (slice(None), ["CHP"])] += 100

        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Elec"])] -= 0.4
        regional_parameters["reg1"]["carrier_ratio_out"].loc[:, (['CHP'], ["Heat"])] -= 0.6

        # Imposing a maximum production 
        regional_parameters["reg1"]["tech_min_production_share"].loc[:, (slice(None), ["PV_park"])] += 0.1
        regional_parameters["reg1"]["Conv_plus_min_production_share"].loc[:, (['CHP'], ["Elec"])] += 0.1

        model_data = ModelData(
            settings,
            settings.default_global_parameters,
            settings.default_trade_parameters,
            regional_parameters
        )

        model = BuildModel(model_data=model_data)
        results = model._solve(verbosity=False, solver="SCIPY")

        # Check that we used PV_park to produced elec 
        supply_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Supply"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Supply"],
        )

        CHP_technology_use = pd.DataFrame(
            data=results.technology_prod["reg1"]["Conversion_plus"].value,
            index=pd.MultiIndex.from_product(
                [settings.years, settings.time_steps],
                names=["Years", "Timesteps"],
            ),
            columns=settings.technologies["reg1"]["Conversion_plus"],
        )
        
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"].values),5), [2628])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][0:8760].values),5), [876])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][8760:17520].values),5), [876])
        self.assertEqual(round(np.sum(supply_technology_use["PV_park"][17520:26280].values),5), [876])
        
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"].values)*0.6 , 5), [2628])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][0:8760].values)*0.6 , 5), [876])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][8760:17520].values)*0.6 , 5), [876])
        self.assertEqual(round(np.sum(CHP_technology_use["CHP"][17520:26280].values)*0.6 , 5), [876])