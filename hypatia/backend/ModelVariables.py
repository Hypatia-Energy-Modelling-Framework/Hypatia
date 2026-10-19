from hypatia.backend.ModelData import ModelData
from hypatia.utility.constants import ModelMode
from hypatia.utility.utility import *
import numpy as np
import cvxpy as cp
from collections import defaultdict


class ModelVariables():
    def __init__(self, model_data: ModelData):
        self.model_data = model_data
        
        # decision variables
        self.technology_prod = self.create_technology_prod()
        self.technology_use = self.create_technology_use()
        self.line_import = self.create_line_import_export()
        self.line_export = self.create_line_import_export()
        self.new_capacity = self.create_new_capacity()
        self.line_new_capacity = self.create_line_new_capacity()
        self.unmetdemandbycarrier = self.create_unmet_demand_by_carrier()
        # -- boolean decision variables --
        self.boolean_for_minpower = self.create_boolean_for_minpower()
        self.boolean_for_storage = self.create_boolean_for_storage()

        # intermediate variables
        self._balance_()
        if self.model_data.settings.mode == ModelMode.Planning:
            self._calc_variable_planning()

            if self.model_data.settings.multi_node:
                self._calc_variable_planning_line()

        elif self.model_data.settings.mode == ModelMode.Operation:
            self._calc_variable_operation()
            if self.model_data.settings.multi_node:
                self._calc_variable_operation_line()
        
        self._calc_variable_storage_SOC()
        self._calc_emission_variables()
        
        if self.model_data.settings.mode == ModelMode.Planning:
            self._calc_regional_cost_planning()

            if not self.model_data.settings.multi_node:
                self._calc_tot_cost_singlenode()
            else:
                self._calc_lines_cost_planning()
                self._calc_tot_cost_multinode()

        elif self.model_data.settings.mode == ModelMode.Operation:
            self._calc_regional_cost_operation()

            if not self.model_data.settings.multi_node:
                self._calc_tot_cost_singlenode()
            else:
                self._calc_lines_cost_operation()
                self._calc_tot_cost_multinode()
                
        self._calc_regional_emission()
        self._calc_tot_emission()

        # Reshape the demand
        self.demand = {reg: self.model_data.regional_parameters[reg]["demand"] for reg in self.model_data.settings.regions}
        
        self.carrier_ratio_in = {}
        for reg in self.model_data.settings.regions:
            if "Conversion_plus" not in self.model_data.settings.technologies[reg].keys(): 
                continue
            self.carrier_ratio_in[reg] = self.model_data.regional_parameters[reg]["carrier_ratio_in"]
            
        self.carrier_ratio_out = {}
        for reg in self.model_data.settings.regions:
            if "Conversion_plus" not in self.model_data.settings.technologies[reg].keys(): 
                continue
            self.carrier_ratio_out[reg] = self.model_data.regional_parameters[reg]["carrier_ratio_out"]
        
    """
    Primary variables
    """
    def create_technology_prod(self):
        """
        Create a dictionary of production variables for each technology in each region.
    
        The method initializes a hierarchical structure of variables representing the production
        levels of technologies, categorized by region and technology type. The variables are 
        defined as non-negative, ensuring that production cannot fall below zero.
    
        Returns:
            technology_prod (dict): A dictionary structured as:
                {
                    "region1": {
                        "tech_category1": cp.Variable(shape=(num_time_intervals, num_technologies), nonneg=True),
                        "tech_category2": cp.Variable(shape=(num_time_intervals, num_technologies), nonneg=True),
                        ...
                    },
                    "region2": {
                        ...
                    },
                    ...
                }
        """
        # Initialize an empty dictionary to hold the production variables for all regions
        technology_prod = {}
        # Iterate over each region in the model settings
        for reg in self.model_data.settings.regions:
            # Initialize a dictionary to hold production variables for each technology category in the region
            regional_prod = {}
            # Iterate over technology categories available in the current region
            for technology_category in self.model_data.settings.technologies[reg].keys():
                # Skip the "Demand" category as it does not represent a production technology
                if technology_category != "Demand":
                    # Define a cvxpy variable for production levels of the current technology category
                    # Shape:
                    #   - Rows: Total number of time intervals (years * time_steps)
                    #   - Columns: Number of technologies in the category
                    # Constraint: Variables must be non-negative
                    regional_prod[technology_category] = cp.Variable(
                        shape=(
                            len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),  # Total time intervals
                            len(self.model_data.settings.technologies[reg][technology_category]),          # Number of technologies
                        ),
                        nonneg=True  # Ensure non-negative values
                    )    
            # Add the regional production dictionary to the main dictionary
            technology_prod[reg] = regional_prod
        # Return the complete dictionary of technology production variables
        return technology_prod

    def create_technology_use(self):
        """
        Create a dictionary of utilization variables for each technology in each region.
    
        This method initializes a hierarchical structure of variables representing the 
        utilization of technologies over time, categorized by region and technology type.
        Excludes "Demand" and "Supply" categories since they do not represent active utilization.
    
        Returns:
            technology_use (dict): A dictionary structured as:
                {
                    "region1": {
                        "tech_category1": cp.Variable(shape=(num_time_intervals, num_technologies), nonneg=True),
                        "tech_category2": cp.Variable(shape=(num_time_intervals, num_technologies), nonneg=True),
                        ...
                    },
                    "region2": {
                        ...
                    },
                    ...
                }
        """
        # Initialize an empty dictionary to hold the utilization variables for all regions
        technology_use = {}
        excluded_categories = {"Demand", "Supply"}
    
        # Iterate over each region in the model settings
        for reg in self.model_data.settings.regions:
            # Initialize a dictionary to hold utilization variables for each technology category in the region
            regional_use = {}
            # Iterate over technology categories available in the current region
            for technology_category in self.model_data.settings.technologies[reg].keys():
                
                # Skip "Demand" and "Supply" categories as they do not require utilization variables
                if technology_category not in excluded_categories:
                    # Define a cvxpy variable for utilization levels of the current technology category
                    # Shape:
                    #   - Rows: Total number of time intervals (years * time_steps)
                    #   - Columns: Number of technologies in the category
                    # Constraint: Variables must be non-negative
                    if technology_category == "Storage":
                    # Allow negative values for "Storage" utilization
                        regional_use[technology_category] = cp.Variable(
                            shape=(
                                len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),
                                len(self.model_data.settings.technologies[reg][technology_category]),
                            ),
                            nonneg=True
                        )
                    else:
                        # Keep non-negative constraint for other technology categories
                        regional_use[technology_category] = cp.Variable(
                            shape=(
                                len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),
                                len(self.model_data.settings.technologies[reg][technology_category]),
                            ),
                            nonneg=True
                        )
            # Add the regional utilization dictionary to the main dictionary
            technology_use[reg] = regional_use
    
        # Return the complete dictionary of technology utilization variables
        return technology_use

    def create_line_import_export(self):
        """
        Create a dictionary of import/export variables for energy/resource flows between regions.
    
        This method initializes variables for multi-node energy systems to track inter-regional 
        flows of carriers (e.g., electricity, gas) over time. If the model is not configured 
        for multi-node mode, the function returns `None`.
    
        Returns:
            import_export (dict or None): A dictionary structured as:
                {
                    "region1": {
                        "region2": cp.Variable(shape=(num_time_intervals, num_carriers), nonneg=True),
                        "region3": cp.Variable(shape=(num_time_intervals, num_carriers), nonneg=True),
                        ...
                    },
                    "region2": {
                        ...
                    },
                    ...
                }
            Or `None` if the model is in single-node mode.
        """
        # Check if the model is in multi-node mode
        if not self.model_data.settings.multi_node:
            return None  # Return None for single-node models
    
        # Initialize an empty dictionary to hold import/export variables for all regions
        import_export = {}
    
        # Iterate over each region in the model settings
        for reg in self.model_data.settings.regions:
            # Initialize a dictionary to hold import/export variables for flows from the current region
            regional_import_export = {}
    
            # Iterate over other regions to define flows between regions
            for other_reg in self.model_data.settings.regions:
                # Avoid creating variables for flows within the same region
                if reg != other_reg:
                    # Define a cvxpy variable for import/export flows from reg to other_reg
                    # Shape:
                    #   - Rows: Total number of time intervals (years * time_steps)
                    #   - Columns: Number of carriers (e.g., electricity, gas)
                    # Constraint: Variables must be non-negative
                    regional_import_export[other_reg] = cp.Variable(
                        shape=(
                            len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),  # Total time intervals
                            len(self.model_data.settings.global_settings["Carriers_glob"].index),           # Number of carriers
                        ),
                        nonneg=True  # Ensure non-negative values
                    )
            
            # Add the regional import/export dictionary to the main dictionary
            import_export[reg] = regional_import_export
    
        # Return the complete dictionary of import/export variables
        return import_export

    def create_new_capacity(self):
        if self.model_data.settings.mode != ModelMode.Planning:
            return None

        new_capacity = {}
        for reg in self.model_data.settings.regions:
            regional_new_capacity = {}
            for tech_type in self.model_data.settings.technologies[reg].keys():
                if tech_type != "Demand":
                    
                    # Get input of modul tech unit from the proper input files
                    new_capacity_by_tech_type = []
                    step_by_techs = get_parameters_from_global_or_regional_file(
                        self.model_data.settings, 
                        self.model_data,
                        "global_new_capacity_step",
                        "new_capacity_step"
                    )
                    
                    # Apply MILP only for variables that requires it, otherwise take LP
                    for tech in self.model_data.settings.technologies[reg][tech_type]:
                        tech_step = step_by_techs.loc[:, tech_type].loc[:, tech].values[0]

                        if tech_step > 0:
                            n = cp.Variable(
                                shape=(len(self.model_data.settings.years), 1),
                                integer=True,
                            )
                            new_capacity_by_tech = cp.multiply(n, tech_step)
                        else:
                            new_capacity_by_tech = cp.Variable(
                                shape=(len(self.model_data.settings.years), 1),
                            )

                        new_capacity_by_tech_type.append(new_capacity_by_tech)
                    regional_new_capacity[tech_type] = cp.hstack(new_capacity_by_tech_type)

            new_capacity[reg] = regional_new_capacity
        return new_capacity

    def create_line_new_capacity(self):
        """
        Create a dictionary of variables for new capacity additions on transmission lines.
    
        This method initializes variables to represent the additional capacity to be installed
        on inter-regional transmission lines over a planning horizon. It is applicable only 
        for multi-node systems in `ModelMode.Planning`.
    
        Returns:
            line_newcapacity (dict or None): A dictionary structured as:
                {
                    "line1": cp.Variable(shape=(num_years, num_carriers), nonneg=True),
                    "line2": cp.Variable(shape=(num_years, num_carriers), nonneg=True),
                    ...
                }
            Or `None` if the model is not in planning mode or is single-node.
        """
        # Ensure the model is in planning mode
        if self.model_data.settings.mode != ModelMode.Planning:
            return None  # Return None if not in planning mode
    
        # Ensure the model is multi-node
        if not self.model_data.settings.multi_node:
            return None  # Return None if the model is single-node
    
        # Initialize an empty dictionary to hold new capacity variables for all transmission lines
        line_newcapacity = {}
    
        # Iterate over each line in the list of transmission lines
        for line in self.model_data.settings.lines_list:
            # Define a cvxpy variable for new capacity additions on the current line
            # Shape:
            #   - Rows: Number of years in the planning horizon
            #   - Columns: Number of carriers (e.g., electricity, gas)
            # Constraint: Variables must be non-negative
            line_newcapacity[line] = cp.Variable(
                shape=(
                    len(self.model_data.settings.years),  # Total years
                    len(self.model_data.settings.global_settings["Carriers_glob"].index),  # Number of carriers
                ),
                nonneg=True  # Ensure non-negative values
            )
    
        # Return the complete dictionary of new capacity variables for transmission lines
        return line_newcapacity

    def create_unmet_demand_by_carrier(self):
        """
        Create a dictionary of unmet demand variables for each carrier in each region.
    
        This method initializes variables representing the unmet demand for carriers
        (e.g., electricity, gas) in different regions over time. Unmet demand occurs
        when the supply of a carrier cannot fully meet the demand.
    
        Returns:
            unmetdemandbycarrier (dict): A nested dictionary structured as:
                {
                    "region1": {
                        "carrier1": cp.Variable(shape=(num_time_intervals,), nonneg=True),
                        "carrier2": cp.Variable(shape=(num_time_intervals,), nonneg=True),
                        ...
                    },
                    "region2": {
                        ...
                    },
                    ...
                }
        """
        # Initialize an empty dictionary to hold unmet demand variables for all regions
        unmetdemandbycarrier = {}
    
        # Iterate over each region in the model settings
        for reg in self.model_data.settings.regions:
            # Initialize a dictionary to hold unmet demand variables for each carrier in the region
            unmetdemandbycarrier_regional = {}
    
            # Iterate over each carrier in the global settings
            for carr in self.model_data.settings.global_settings["Carriers_glob"]["Carrier"]:
                # Initialize an array of zeros to represent unmet demand for the carrier
                # This will be populated with cvxpy variables if applicable
                unmetdemandbycarrier_regional[carr] = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),)
                )
    
                # Iterate over all technology categories in the region
                for key in self.model_data.settings.technologies[reg].keys():
                    # Skip non-demand categories, as only "Demand" technologies are relevant
                    if key != "Demand":
                        continue
    
                    # Iterate over all technologies in the "Demand" category
                    for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):
                        # Check if the current technology uses the carrier being processed
                        if carr in self.model_data.settings.regional_settings[reg]["Carrier_input"]\
                            .loc[
                                self.model_data.settings.regional_settings[reg]["Carrier_input"]["Technology"] == tech
                            ]["Carrier_in"].values:
                            # Add a cvxpy variable for unmet demand to the carrier's array
                            unmetdemandbycarrier_regional[carr] += cp.Variable(
                                shape=(
                                    len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),
                                ),
                                nonneg=True,  # Ensure non-negative values
                            )
    
            # Add the regional unmet demand dictionary to the main dictionary
            unmetdemandbycarrier[reg] = unmetdemandbycarrier_regional
    
        # Return the complete dictionary of unmet demand variables
        return unmetdemandbycarrier
    
    def create_boolean_for_minpower(self):
        """
        Create a dictionary of boolean variables for each generation technology in each region.
    
        The method initializes a hierarchical structure of variables representing the flag of each
        generation technology, categorized by region and technology type. The variables are 
        defined as boolean, ensuring that the technology can generate flows above a minimum treshold 
        or nothing.
    
        Returns:
            boolean_for_minpower (dict): A dictionary structured as:
                {
                    "region1": {
                        "regional_boolean1": cp.Variable(shape=(num_time_intervals, num_storage_techs), boolean=True),
                        "regional_boolean2": cp.Variable(shape=(num_time_intervals, num_storage_techs), boolean=True),
                        ...
                    },
                    "region2": {
                        ...
                    },
                    ...
                }
        """
        # Initialize an empty dictionary to hold the boolean variables for all regions
        boolean_for_minpower = {}
        
        # Iterate over each region in the model settings
        for reg in self.model_data.settings.regions:
            # Initialize a dictionary to hold boolean variables for each technology category in the region
            reg_boolean_for_minpower = {}
            # Iterate over technology categories available in the current region
            for technology_category in self.model_data.settings.technologies[reg].keys():
                # Skip the "Demand","Transmission" and "Storage" categories as they do not represent generation technologies
                if technology_category not in ["Demand", "Transmission", "Storage"]:
                    # Define a cvxpy variable for booleans of the current technology category
                    # Shape:
                    #   - Rows: Total number of time intervals (years * time_steps)
                    #   - Columns: Number of generation technologies in the category
                    # Constraint: Variables must be boolean
                    reg_boolean_for_minpower[technology_category] = cp.Variable(
                        shape=(
                            len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),  # Total time intervals
                            len(self.model_data.settings.technologies[reg][technology_category]),          # Number of technologies
                        ),
                        boolean = True
                    )    
            # Add the regional dictionary to the main dictionary
            boolean_for_minpower[reg] = reg_boolean_for_minpower
            
        # Return the complete dictionary of storage boolean variables
        return boolean_for_minpower
    
    def create_boolean_for_storage(self):
        """
        Create a dictionary of boolean variables for each storage technology in each region.
    
        The method initializes a hierarchical structure of variables representing the direction of
        flows of storage technologies, categorized by region and technology type. The variables are 
        defined as boolean, ensuring that production and use can't occur simultaneously.
    
        Returns:
            boolean_for_storage (dict): A dictionary structured as:
                {
                    "region1": {
                        "reg_boolean_for_storage1": cp.Variable(shape=(num_time_intervals, num_storage_techs), boolean=True),
                        "reg_boolean_for_storage2": cp.Variable(shape=(num_time_intervals, num_storage_techs), boolean=True),
                        ...
                    },
                    "region2": {
                        ...
                    },
                    ...
                }
        """
        # Initialize an empty dictionary to hold the boolean variables for all regions
        boolean_for_storage = {}
        
        # Iterate over each region in the model settings
        for reg in self.model_data.settings.regions:
            # Initialize a dictionary to hold boolean variables for each technology category in the region
            reg_boolean_for_storage = {}
            # Iterate over technology categories available in the current region
            for technology_category in self.model_data.settings.technologies[reg].keys():
                # Skip the "Demand" category as it does not represent a production technology
                if technology_category == "Storage":
                    # Define a cvxpy variable for booleans of the current Storage technology category
                    # Shape:
                    #   - Rows: Total number of time intervals (years * time_steps)
                    #   - Columns: Number of Storage technologies in the category
                    # Constraint: Variables must be boolean
                    reg_boolean_for_storage[technology_category] = cp.Variable(
                        shape=(
                            len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),  # Total time intervals
                            len(self.model_data.settings.technologies[reg][technology_category]),          # Number of technologies
                        ),
                        boolean = True
                    )    
            # Add the regional dictionary to the main dictionary
            boolean_for_storage[reg] = reg_boolean_for_storage
            
        # Return the complete dictionary of storage boolean variables
        return boolean_for_storage


    
    """
    Secondary variables
    """
    def _calc_variable_planning(self):

        """
        Calculates all the cost components of the objective function and the
        intermediate variables in the planning mode, for each region
        """

        self.real_new_capacity = {}
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
        self.production_annual = {}
        self.consumption_annual = {}
        self.land_usage = {}
        self.residual_capacity = {}
        self.unmet_demand_annual = {}
        self.cost_unmet_demand = {}

        for reg in self.model_data.settings.regions:
            
            real_new_capacity_regional = {}
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
            production_annual_regional = {}
            consumption_annual_regional = {}
            land_usage_regional = {}
            residual_capacity_regional = {}
            unmet_demand_annual_regional = {}
            cost_unmet_demand_regional = {}

            for key in self.new_capacity[reg].keys():

                real_new_capacity_regional[key] = shift_new_cap(
                    self.new_capacity[reg][key], 
                    self.model_data.settings.technologies[reg][key], 
                    self.model_data.regional_parameters[reg]["time_of_construction"].loc[:, key],
                    self.model_data.settings.years)

                (
                    cost_inv_regional[key],
                    cost_inv_tax_regional[key],
                    cost_inv_sub_regional[key],
                ) = invcosts(
                    self.model_data.regional_parameters[reg]["tech_inv"][key],
                    self.new_capacity[reg][key],
                    self.model_data.regional_parameters[reg]["inv_taxsub"]["Tax"][key],
                    self.model_data.regional_parameters[reg]["inv_taxsub"]["Sub"][key],
                )

                salvage_inv_regional[key] = cp.multiply(
                    salvage_factor(
                        self.model_data.settings.years,
                        self.model_data.settings.technologies[reg][key],
                        self.model_data.regional_parameters[reg]["tech_lifetime"].loc[:, key],
                        self.model_data.regional_parameters[reg]["interest_rate"].loc[:, key],
                        self.model_data.regional_parameters[reg]["discount_rate"],
                        self.model_data.regional_parameters[reg]["economic_lifetime"].loc[:, key],
                    ),
                    cost_inv_regional[key],
                )

                accumulated_newcapacity_regional[key] = newcap_accumulated(
                    real_new_capacity_regional[key],
                    self.model_data.settings.technologies[reg][key],
                    self.model_data.settings.years,
                    self.model_data.regional_parameters[reg]["tech_lifetime"].loc[:, key],
                )

                totalcapacity_regional[key] = (
                    accumulated_newcapacity_regional[key]
                    + self.model_data.regional_parameters[reg]["tech_residual_cap"].loc[:, key]
                )

                (
                    cost_fix_regional[key],
                    cost_fix_tax_regional[key],
                    cost_fix_Sub_regional[key],
                ) = fixcosts(
                    self.model_data.regional_parameters[reg]["tech_fixed_cost"][key],
                    totalcapacity_regional[key],
                    self.model_data.regional_parameters[reg]["fix_taxsub"]["Tax"][key],
                    self.model_data.regional_parameters[reg]["fix_taxsub"]["Sub"][key],
                )

                decomcapacity_regional[key] = decomcap(
                    real_new_capacity_regional[key],
                    self.model_data.settings.technologies[reg][key],
                    self.model_data.settings.years,
                    self.model_data.regional_parameters[reg]["tech_lifetime"].loc[:, key],
                )

                cost_decom_regional[key] = cp.multiply(
                    self.model_data.regional_parameters[reg]["tech_decom_cost"].loc[:, key].values,
                    decomcapacity_regional[key],
                )

                production_annual_regional[key] = annual_activity(
                    self.technology_prod[reg][key],
                    self.model_data.settings.years,
                    self.model_data.settings.time_steps,
                )
                
                if key != "Demand" and key != "Supply": 
                
                    consumption_annual_regional[key] = annual_activity(
                        self.technology_use[reg][key],
                        self.model_data.settings.years,
                        self.model_data.settings.time_steps,
                    )            

                cost_variable_regional[key] = cp.multiply(
                    production_annual_regional[key],
                    self.model_data.regional_parameters[reg]["tech_var_cost"].loc[:, key],
                )

                cost_fvalue_regional[key] = invcosts_annuity(
                    cost_inv_regional[key],
                    self.model_data.regional_parameters[reg]["interest_rate"].loc[:, key],
                    self.model_data.regional_parameters[reg]["economic_lifetime"].loc[:, key],
                    self.model_data.settings.technologies[reg][key],
                    self.model_data.settings.years,
                    self.model_data.regional_parameters[reg]["discount_rate"],
                )  
                
                land_usage_regional[key] = cp.multiply(
                    totalcapacity_regional[key],self.model_data.regional_parameters[reg]["specific_land_usage"].loc[:, key]
                ) 
                
                residual_capacity_regional[key] = self.model_data.regional_parameters[reg]["tech_residual_cap"].loc[:, key]
                
               
            for carr in self.unmetdemandbycarrier[reg].keys():
            
                unmet_demand_annual_regional[carr] = unmet_demand_function(
                    self.unmetdemandbycarrier[reg][carr],
                    self.model_data.settings.years,
                    self.model_data.settings.time_steps                
                    )
            
                cost_unmet_demand_regional[carr] = unmet_demand_annual_regional[carr] * 1e10
                
            self.real_new_capacity[reg] = real_new_capacity_regional
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
            self.cost_inv_fvalue[reg] = cost_fvalue_regional
            self.production_annual[reg] = production_annual_regional
            self.consumption_annual[reg] = consumption_annual_regional
            self.land_usage[reg] = land_usage_regional
            self.residual_capacity[reg] = residual_capacity_regional 
            self.unmet_demand_annual[reg] = unmet_demand_annual_regional 
            self.cost_unmet_demand[reg] = cost_unmet_demand_regional
            

    def _calc_variable_planning_line(self):

        """
        Calculates all the cost and intermediate variables related to the inter-
        regional links in the planning mode
        """

        self.real_new_line_capacity = {}
        self.cost_inv_line = {}
        self.line_accumulated_newcapacity = {}
        self.line_totalcapacity = {}
        self.cost_fix_line = {}
        self.line_decommissioned_capacity = {}
        self.cost_decom_line = {}

        for key in self.line_new_capacity.keys():
            
            self.real_new_line_capacity[key] = shift_new_line_cap(
                self.line_new_capacity[key], 
                self.model_data.settings.global_settings["Carriers_glob"]["Carrier"], 
                self.model_data.trade_parameters["line_time_of_construction"].loc[:, key],
                self.model_data.settings.years)

            self.cost_inv_line[key] = cp.multiply(
                self.model_data.trade_parameters["line_inv"].loc[:, key].values,
                self.line_new_capacity[key],
            )

            self.line_accumulated_newcapacity[key] = line_newcap_accumulated(
                self.real_new_line_capacity[key],
                self.model_data.settings.global_settings["Carriers_glob"]["Carrier"],
                self.model_data.settings.years,
                self.model_data.trade_parameters["line_lifetime"].loc[:, key],
            )

            self.line_totalcapacity[key] = (
                self.line_accumulated_newcapacity[key]
                + self.model_data.trade_parameters["line_residual_cap"].loc[:, key].values
            )

            self.cost_fix_line[key] = cp.multiply(
                self.model_data.trade_parameters["line_fixed_cost"].loc[:, key].values,
                self.line_totalcapacity[key],
            )

            self.line_decommissioned_capacity[key] = line_decomcap(
                self.real_new_line_capacity[key],
                self.model_data.settings.global_settings["Carriers_glob"]["Carrier"],
                self.model_data.settings.years,
                self.model_data.trade_parameters["line_lifetime"].loc[:, key],
            )

            self.cost_decom_line[key] = cp.multiply(
                self.model_data.trade_parameters["line_decom_cost"].loc[:, key].values,
                self.line_decommissioned_capacity[key],
            )
            
        
        self.cost_variable_line = line_varcost(
            self.model_data.trade_parameters["line_var_cost"],
            self.line_import,
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.time_steps,
            self.model_data.settings.lines_list,
        )
        
        self.line_import_annual = line_annual_activity(
            self.line_import,
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.time_steps,
            )
        
        self.line_export_annual = line_annual_activity(
            self.line_export,
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.time_steps,
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
        self.production_annual = {}
        self.consumption_annual = {}
        self.residual_capacity = {}
        self.unmet_demand_annual = {} 
        self.cost_unmet_demand = {}
        
        for reg in self.model_data.settings.regions:

            totalcapacity_regional = {}
            cost_fix_regional = {}
            cost_fix_tax_regional = {}
            cost_fix_Sub_regional = {}
            cost_variable_regional = {}
            production_annual_regional = {}
            consumption_annual_regional = {}
            residual_capacity_regional = {}
            unmet_demand_annual_regional = {}
            cost_unmet_demand_regional = {}            

            for key in self.model_data.settings.technologies[reg].keys():

                if key != "Demand":

                    totalcapacity_regional[key] = (
                        self.model_data.regional_parameters[reg]["tech_residual_cap"].loc[:, key].values
                    )

                    (
                        cost_fix_regional[key],
                        cost_fix_tax_regional[key],
                        cost_fix_Sub_regional[key],
                    ) = fixcosts(
                        self.model_data.regional_parameters[reg]["tech_fixed_cost"][key],
                        totalcapacity_regional[key],
                        self.model_data.regional_parameters[reg]["fix_taxsub"]["Tax"][key],
                        self.model_data.regional_parameters[reg]["fix_taxsub"]["Sub"][key],
                    )

                    production_annual_regional[key] = annual_activity(
                        self.technology_prod[reg][key],
                        self.model_data.settings.years,
                        self.model_data.settings.time_steps,
                    )
                    
                    if key != "Demand" and key != "Supply": 
                    
                        consumption_annual_regional[key] = annual_activity(
                            self.technology_use[reg][key],
                            self.model_data.settings.years,
                            self.model_data.settings.time_steps,
                        ) 
                    
                    cost_variable_regional[key] = cp.multiply(
                        production_annual_regional[key],
                        self.model_data.regional_parameters[reg]["tech_var_cost"].loc[:, key],
                    )
                    
                    residual_capacity_regional[key] = self.model_data.regional_parameters[reg]["tech_residual_cap"].loc[:, key]
                    
            for carr in self.unmetdemandbycarrier[reg].keys():
                
                unmet_demand_annual_regional[carr] = unmet_demand_function(
                    self.unmetdemandbycarrier[reg][carr],
                    self.model_data.settings.years,
                    self.model_data.settings.time_steps                
                    )
            
                cost_unmet_demand_regional[carr] = unmet_demand_annual_regional[carr] * 1e10

            self.totalcapacity[reg] = totalcapacity_regional
            self.cost_fix[reg] = cost_fix_regional
            self.cost_fix_tax[reg] = cost_fix_tax_regional
            self.cost_fix_sub[reg] = cost_fix_Sub_regional
            self.cost_variable[reg] = cost_variable_regional
            self.production_annual[reg] = production_annual_regional
            self.consumption_annual[reg] = consumption_annual_regional
            self.residual_capacity[reg] = residual_capacity_regional
            self.unmet_demand_annual[reg] = unmet_demand_annual_regional 
            self.cost_unmet_demand[reg] = cost_unmet_demand_regional
        

    def _calc_variable_operation_line(self):

        """
        Calculates all the cost and intermediate variables related to the inter-
        regional links in the operation mode
        """

        self.line_totalcapacity = {}
        self.cost_fix_line = {}
        for key in self.model_data.settings.lines_list:

            self.line_totalcapacity[key] = (
                self.model_data.trade_parameters["line_residual_cap"].loc[:, key].values
            )
            self.cost_fix_line[key] = cp.multiply(
                self.model_data.trade_parameters["line_fixed_cost"].loc[:, key].values,
                self.line_totalcapacity[key],
            )

        self.cost_variable_line = line_varcost(
            self.model_data.trade_parameters["line_var_cost"],
            self.line_import,
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.time_steps,
            self.model_data.settings.lines_list,
        )
        
        self.line_import_annual = line_annual_activity(
            self.line_import,
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.time_steps,
            )
        
        self.line_export_annual = line_annual_activity(
            self.line_export,
            self.model_data.settings.regions,
            self.model_data.settings.years,
            self.model_data.settings.time_steps,
            )

    def _calc_variable_storage_SOC(self):

        """
        Calculates the annual state of charge of the on grid storage technologies,
        in the models with hourly temporal resolution
        """

        self.storage_SOC = {}

        # The cycle-duration parameter is required (and read) only when some
        # region has storage: without storage there is nothing to compute, and
        # reading it would fail with a KeyError.
        if not list(get_regions_with_storage(self.model_data.settings)):
            return

        timesteps_per_cycle = get_parameters_from_global_or_regional_file(
                self.model_data.settings, 
                self.model_data, 
                "golabl_storage_cyclic_boundary",
                "storage_cyclic_boundary"
                )
        
        for reg in get_regions_with_storage(self.model_data.settings):
            
            self.storage_SOC[reg] = storage_state_of_charge(
                self.technology_use[reg]["Storage"],
                self.technology_prod[reg]["Storage"],
                self.model_data.settings.years,
                self.model_data.settings.time_steps,
                timesteps_per_cycle,
                self.model_data.regional_parameters[reg]["storage_charge_efficiency"],
                self.model_data.regional_parameters[reg]["storage_discharge_efficiency"],
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

        for reg in self.model_data.settings.regions:

            totalusebycarrier_regional = {}
            totalprodbycarrier_regional = {}
            totalimportbycarrier_regional = {}
            totalexportbycarrier_regional = {}
            totaldemandbycarrier_regional = {}

            for carr in self.model_data.settings.global_settings["Carriers_glob"]["Carrier"]:

                totalusebycarrier_regional[carr] = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),)
                )
                totalprodbycarrier_regional[carr] = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),)
                )
                totalimportbycarrier_regional[carr] = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),)
                )
                totalexportbycarrier_regional[carr] = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),)
                )
                totaldemandbycarrier_regional[carr] = np.zeros(
                    (len(self.model_data.settings.years) * len(self.model_data.settings.time_steps),)
                )                             

                for key in self.model_data.settings.technologies[reg].keys():

                    for indx, tech in enumerate(self.model_data.settings.technologies[reg][key]):

                        if (
                            carr
                            in self.model_data.settings.regional_settings[reg]["Carrier_input"]
                            .loc[
                                self.model_data.settings.regional_settings[reg]["Carrier_input"]["Technology"]
                                == tech
                            ]["Carrier_in"]
                            .values
                        ):

                            if key == "Conversion_plus":

                                totalusebycarrier_regional[carr] += cp.multiply(
                                    self.technology_use[reg][key][
                                        :, indx
                                    ],
                                    self.model_data.regional_parameters[reg]["carrier_ratio_in"][
                                        (tech, carr)
                                    ].values,
                                )

                            elif key == "Demand":

                                totaldemandbycarrier_regional[carr] += self.model_data.regional_parameters[
                                    reg
                                ]["demand"][tech].values                                

                            elif key != "Supply":

                                totalusebycarrier_regional[carr] += self.technology_use[reg][key][:, indx]

                        if (
                            carr
                            in self.model_data.settings.regional_settings[reg]["Carrier_output"]
                            .loc[
                                self.model_data.settings.regional_settings[reg]["Carrier_output"]["Technology"]
                                == tech
                            ]["Carrier_out"]
                            .values
                        ):
                            if key == "Conversion_plus":

                                totalprodbycarrier_regional[carr] += cp.multiply(
                                    self.technology_prod[reg][key][
                                        :, indx
                                    ],
                                    self.model_data.regional_parameters[reg]["carrier_ratio_out"][
                                        (tech, carr)
                                    ].values,
                                )
                            else:

                                totalprodbycarrier_regional[carr] += self.technology_prod[reg][key][:, indx]

                if len(self.model_data.settings.regions) > 1:

                    for key in self.line_import[reg].keys():

                        if "{}-{}".format(reg, key) in self.model_data.settings.lines_list:

                            line_eff = (
                                pd.concat(
                                    [
                                        self.model_data.trade_parameters["line_eff"][
                                            ("{}-{}".format(reg, key), carr)
                                        ]
                                    ]
                                    * len(self.model_data.settings.time_steps)
                                )
                                .sort_index()
                                .values
                            )
                            
                            line_length = (
                                pd.concat(
                                    [
                                        self.model_data.trade_parameters["line_length"][
                                            ("{}-{}".format(reg, key), carr)
                                        ]
                                    ]
                                    * len(self.model_data.settings.time_steps)
                                )
                                .sort_index()
                                .values
                            )

                        elif "{}-{}".format(key, reg) in self.model_data.settings.lines_list:

                            line_eff = (
                                pd.concat(
                                    [
                                        self.model_data.trade_parameters["line_eff"][
                                            ("{}-{}".format(key, reg), carr)
                                        ]
                                    ]
                                    * len(self.model_data.settings.time_steps)
                                )
                                .sort_index()
                                .values
                            )
                            
                            line_length = (
                                pd.concat(
                                    [
                                        self.model_data.trade_parameters["line_length"][
                                            ("{}-{}".format(key, reg), carr)
                                        ]
                                    ]
                                    * len(self.model_data.settings.time_steps)
                                )
                                .sort_index()
                                .values
                            )
                            
                        # efficiency per 100 length units, compounded over the line
                        # length: eff ** (length / 100). Both are input data, so this
                        # is computed with numpy: written with cp.exp it became an
                        # exponential cone that LP solvers (HiGHS, Gurobi LP) reject.
                        line_efficiency = np.power(
                            np.asarray(line_eff, dtype=float),
                            np.asarray(line_length, dtype=float) * 0.01,
                        )

                        totalimportbycarrier_regional[carr] += cp.multiply(
                            self.line_import[reg][key][
                                :,
                                list(
                                    self.model_data.settings.global_settings["Carriers_glob"]["Carrier"]
                                ).index(carr),
                            ],
                            line_efficiency,
                        )

                        totalexportbycarrier_regional[carr] += self.line_export[reg][key][
                                :,
                                list(
                                    self.model_data.settings.global_settings["Carriers_glob"]["Carrier"]
                                ).index(carr),
                            ]
            
            self.totalusebycarrier[reg] = totalusebycarrier_regional
            self.totalprodbycarrier[reg] = totalprodbycarrier_regional
            self.totalimportbycarrier[reg] = totalimportbycarrier_regional
            self.totalexportbycarrier[reg] = totalexportbycarrier_regional
            self.totaldemandbycarrier[reg] = totaldemandbycarrier_regional


    def _calc_emission_variables(self):
        self.emission_by_region = {}
        self.captured_emission_by_region = {}
        self.emission_cost_by_region = {}
        self.used_emissions_by_region = {}
        self.emission_by_type = {}
        self.captured_emission_by_type = {}
        self.emission_cost_by_type = {}
        self.used_emissions_by_type = {}

        for reg in self.model_data.settings.regions:
            emissions_regional = defaultdict(dict)
            emission_cost_regional = defaultdict(dict)
            total_captured_emissions_regional = defaultdict(dict)
            used_emissions_regional = defaultdict(dict)
            for key in self.model_data.settings.technologies[reg].keys():
                if key == "Demand" or key == "Transmission" or key == "Storage":
                # if key == "Demand" or key == "Transmission":   
                    continue

                for emission_type in get_emission_types(self.model_data.settings.global_settings):

                    regional_emissions = []
                    total_captured_emissions = []
                    used_emissions = []                    
                    
                    for indx,tech in enumerate(self.model_data.regional_parameters[reg]["specific_emission"][emission_type].loc[:, key]):
                        if self.model_data.regional_parameters[reg]["specific_emission"][emission_type].loc[:, key].iloc[:,indx].values[0] >= 0:
                            
                            regional_emissions.append(cp.reshape(cp.multiply(
                                self.production_annual[reg][key][:,indx],
                                cp.multiply(self.model_data.regional_parameters[reg]["specific_emission"][emission_type].loc[:, key].iloc[:,indx].values,
                                (np.ones((len(self.model_data.settings.years),))
                                 -self.model_data.regional_parameters[reg]["emission_capture_efficiency"][emission_type].loc[:, key].iloc[:,indx].values))), 
                                (len(self.model_data.settings.years),1)
                            ))
                            
                            total_captured_emissions.append(cp.reshape(cp.multiply(
                                self.production_annual[reg][key][:,indx],
                                cp.multiply(self.model_data.regional_parameters[reg]["specific_emission"][emission_type].loc[:, key].iloc[:,indx].values,
                                self.model_data.regional_parameters[reg]["emission_capture_efficiency"][emission_type].loc[:, key].iloc[:,indx].values)), 
                                (len(self.model_data.settings.years),1)
                            ))
                            
                            used_emissions.append(cp.reshape(cp.multiply(
                                self.production_annual[reg][key][:,indx],
                                np.zeros((self.production_annual[reg][key][:,indx].shape[0],))),
                                (len(self.model_data.settings.years),1)
                            ))
                            
                        else:
                            # Negative emission factor: technology removes emissions (e.g. BECCS, DAC).
                            # Pass the negative value through to emission_by_region so it reduces totals.
                            regional_emissions.append(cp.reshape(cp.multiply(
                                self.production_annual[reg][key][:,indx],
                                self.model_data.regional_parameters[reg]["specific_emission"][emission_type].loc[:, key].iloc[:,indx].values),
                                (len(self.model_data.settings.years),1)
                            ))                
                                          
                            # regional_emissions.append(cp.reshape(cp.multiply(
                            #     self.production_annual[reg][key][:,indx],
                            #     np.zeros((self.production_annual[reg][key][:,indx].shape[0],))),
                            #     (len(self.model_data.settings.years),1)
                            # ))
                            
                            total_captured_emissions.append(cp.reshape(cp.multiply(
                                self.production_annual[reg][key][:,indx],
                                np.zeros((self.production_annual[reg][key][:,indx].shape[0],))),
                                (len(self.model_data.settings.years),1)
                            ))
                            
                            used_emissions.append(cp.reshape(cp.multiply(
                                self.production_annual[reg][key][:,indx],
                                -self.model_data.regional_parameters[reg]["specific_emission"][emission_type].loc[:, key].iloc[:,indx].values),
                                (len(self.model_data.settings.years),1)
                            ))
                    
                    emissions_regional[emission_type][key] = cp.hstack(regional_emissions) 
                    total_captured_emissions_regional[emission_type][key] = cp.hstack(total_captured_emissions) 
                    used_emissions_regional[emission_type][key] = cp.hstack(used_emissions)
                    emission_cost_regional[emission_type][key] = cp.multiply(
                        emissions_regional[emission_type][key],
                        self.model_data.regional_parameters[reg]["emission_tax"][emission_type].loc[:, key],
                    )

            self.emission_by_region[reg] = emissions_regional
            self.captured_emission_by_region[reg] = total_captured_emissions_regional
            self.emission_cost_by_region[reg] = emission_cost_regional
            self.used_emissions_by_region[reg] = used_emissions_regional

        self.emission_by_type = self.flip_keys(self.emission_by_region)
        self.captured_emission_by_type = self.flip_keys(self.captured_emission_by_region)
        self.emission_cost_by_type = self.flip_keys(self.emission_cost_by_region)
        self.used_emissions_by_type = self.flip_keys(self.used_emissions_by_region)


    def flip_keys(self, d):
        result = defaultdict(dict)
        for key, value in d.items():
                for k, v in value.items():
                    result[k][key] = v
        return result
    
    def _calc_regional_cost_planning(self):
        
        self.totalcost_allregions = np.zeros((len(self.model_data.settings.years), 1))
        self.inv_allregions = 0
        years = -1 * np.arange(len(self.model_data.settings.years))

        for reg in self.model_data.settings.regions:

            totalcost_regional = np.zeros((len(self.model_data.settings.years), 1))

            for ctgry in self.model_data.settings.technologies[reg].keys():

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
                        for emission_type in get_emission_types(self.model_data.settings.global_settings):
                            totalcost_regional += cp.sum(
                                self.emission_cost_by_region[reg][emission_type][ctgry], axis=1
                            )
                            
            for carr in self.unmetdemandbycarrier[reg].keys():
                            
                totalcost_regional += cp.sum(self.cost_unmet_demand[reg][carr],axis=1)

            discount_factor = (
                1 + self.model_data.regional_parameters[reg]["discount_rate"]["Annual Discount Rate"].values
            )

            totalcost_regional_discounted = cp.multiply(
                totalcost_regional, np.power(discount_factor, years)
            )
            self.totalcost_allregions += totalcost_regional_discounted
            
    def _calc_regional_cost_operation(self):
        
        self.totalcost_allregions = 0
        for reg in self.model_data.settings.regions:

            totalcost_regional = 0

            for ctgry in self.model_data.settings.technologies[reg].keys():

                if ctgry != "Demand":

                    totalcost_regional += cp.sum(
                        self.cost_fix[reg][ctgry]
                        + self.cost_fix_tax[reg][ctgry]
                        - self.cost_fix_sub[reg][ctgry]
                        + self.cost_variable[reg][ctgry]
                    )

                    if ctgry != "Transmission" and ctgry != "Storage":
                        for emission_type in get_emission_types(self.model_data.settings.global_settings):
                            totalcost_regional += cp.sum(
                                self.emission_cost_by_region[reg][emission_type][ctgry], axis=1
                            )
                            
            for carr in self.unmetdemandbycarrier[reg].keys():
                            
                totalcost_regional += cp.sum(self.cost_unmet_demand[reg][carr],axis=1)

            self.totalcost_allregions += totalcost_regional
            
    def _calc_lines_cost_planning(self):
        
        years = -1 * np.arange(len(self.model_data.settings.years))
        self.totalcost_lines = np.zeros((len(self.model_data.settings.years), 1))

        for line in self.model_data.settings.lines_list:

            self.totalcost_lines += cp.sum(
                self.cost_inv_line[line]
                + self.cost_fix_line[line]
                + self.cost_decom_line[line],
                axis=1,
            )

        for reg in self.model_data.settings.regions:

            for key, value in self.cost_variable_line[reg].items():

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
        
    def _calc_lines_cost_operation(self):
    
        self.totalcost_lines = 0

        for line in self.model_data.settings.lines_list:

            self.totalcost_lines += cp.sum(self.cost_fix_line[line], axis=1)

        for reg in self.model_data.settings.regions:

            for key, value in self.cost_variable_line[reg].items():

                self.totalcost_lines += cp.sum(value, axis=1)
                
    def _calc_tot_cost_singlenode(self):

        if self.model_data.settings.mode == ModelMode.Planning:
            self.tot_cost_single_node = (
                cp.sum(self.totalcost_allregions) + self.inv_allregions
            )

        elif self.model_data.settings.mode == ModelMode.Operation:

            self.tot_cost_single_node = self.totalcost_allregions

    def _calc_tot_cost_multinode(self):

        if self.model_data.settings.mode == ModelMode.Planning:

            self.tot_cost_multi_node = (
                cp.sum(self.totalcost_lines_discounted + self.totalcost_allregions)
                + self.inv_allregions
            )

        elif self.model_data.settings.mode == ModelMode.Operation:

            self.tot_cost_multi_node = self.totalcost_allregions + self.totalcost_lines

    def _calc_regional_emission(self):

        self.totalemission_allregions = np.zeros((len(self.model_data.settings.years), 1))
        
        for reg in self.model_data.settings.regions:
            
            totalemission_regional = np.zeros((len(self.model_data.settings.years), 1))
            
            for emission_type in get_emission_types(self.model_data.settings.global_settings):
                
                totalemission_regional_by_type = np.zeros((len(self.model_data.settings.years), 1))
                
                for ctgry in self.model_data.settings.technologies[reg].keys():

                    if ctgry != "Demand" and ctgry != "Transmission" and ctgry != "Storage":
                        
                        totalemission_regional_by_type += cp.sum(
                            self.emission_by_region[reg][emission_type][ctgry], axis=1
                        )
                        
                totalemission_regional += totalemission_regional_by_type
                
            self.totalemission_allregions += totalemission_regional
            
    def _calc_tot_emission(self):

        if self.model_data.settings.mode == ModelMode.Planning:
            self.tot_emissions = cp.sum(self.totalemission_allregions)

        elif self.model_data.settings.mode == ModelMode.Operation:

            self.tot_emissions = cp.sum(self.totalemission_allregions)
        
            
