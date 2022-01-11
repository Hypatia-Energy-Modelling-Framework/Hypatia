########################################
Building and Running a Model
########################################

.. role:: raw-html(raw)
    :format: html

Building a model
==================

Building a model in Hypatia is very simple and includes three main steps:

#. Defining the **Reference Energy System (RES)**
#. Delivering the structural inputs (sets) to the model through a number of excel-based files
#. Delivering the parameters (data) to the model through a number of excel-based files generated automatically by the model


Reference Energy System (RES)
------------------------------
In order to create the RES based on your model application, you just need the Hypatia terminology to define the correct type of technologies and energy carriers.

Technology categorization
~~~~~~~~~~~~~~~~~~~~~~~~~~
Hypatia uses a technology classification inspired by `Calliope <https://calliope.readthedocs.io/en/stable/index.html>`_ as follows:

.. list-table:: The technology categorization in Hypatia
   :widths: 25 50 50
   :header-rows: 1

   * - Technoloy Category
     - Description
     - Schematic Representation
   * - Supply
     - Supplies an energy carrier to the system without consuming any other carriers
     - .. image:: https://github.com/SESAM-Polimi/Hypatia/blob/main/doc/source/_static/Tech_ctgry/supply.png?raw=true
          :width: 105
          :align: center
   * - Demand
     - Consumes and sinks an energy carrier from the energy system
     - .. image:: https://github.com/SESAM-Polimi/Hypatia/blob/main/doc/source/_static/Tech_ctgry/demand.png?raw=true
          :width: 110
          :align: center
   * - Transmission
     - Transmits an energy carrier locally from a supply point to a demand point
     - .. image:: https://github.com/SESAM-Polimi/Hypatia/blob/main/doc/source/_static/Tech_ctgry/transmission.png?raw=true
          :width: 140
          :align: center
   * - Conversion
     - Converts an energy carrier to another
     - .. image:: https://github.com/SESAM-Polimi/Hypatia/blob/main/doc/source/_static/Tech_ctgry/conversion.png?raw=true
          :width: 140
          :align: center
   * - Conversion_plus
     - Converts one/muliple energy carrier to one/multiple other carriers
     - .. image:: https://github.com/SESAM-Polimi/Hypatia/blob/main/doc/source/_static/Tech_ctgry/conversion_plus.png?raw=true
          :width: 140
          :align: center
   * - Storage
     - Stores and energy carrier and discharge it when it is required 
     - .. image:: https://github.com/SESAM-Polimi/Hypatia/blob/main/doc/source/_static/Tech_ctgry/storage.png?raw=true
          :width: 115
          :align: center 

.. note::

   Currently, there is only the possibility of on-grid utility storage in the hourly resolution. Other types of storage for other temporal resolutions and
   the possibility of connecting a storage facility to another technologies is still under development in the Hypatia framework and it will be available in the
   next version release.

.. note::

   All the technologies in a Hypatia model can have only on carrier input and one carrier output except the technologies within the Conversion-plus category
   which can have multiple carrier inputs and outputs.

Carrier types
~~~~~~~~~~~~~~~~~~~~~~~~~~
besides the technology classifications, hypatia also considers different kinds of energy carriers as follow:

.. list-table:: Different carrier types in a hypatia model
   :widths: 25 50
   :header-rows: 1

   * - Carrier Type
     - Description
   * - Resource
     - The energy resource extracted from the nature (by a supply technology) that are not still processed such as raw oil
   * - Intermediate
     - An energy carrier that can be consumed by **non-Demand** technologies
   * - Demand
     - An energy carrier that can be consumed by **Demand** technologies

.. note::

  The Reference Energy System in a Hypatia model should always starts from Supply technologies (such as resource extraction technologies) and ends with Demand technologies


Definiton of the structural inputs (sets)
-------------------------------------------
The sets of the model must be defined through "n+1" number of excel files in different tables where "n" is the number of regions within the model.
The first excel file defines the global sets and must be named as :guilabel:`&global.xlsx`.
Following tables should be included within the global file:

* **Regions:** Including all the regions within the model with the follwoing columns. The region in a hypatia model has a general definition and can include any geographical scale.
  For example, if the user is modelling the whole world, each region can be the representative of each country or if they are modelling a specific country, each region can be the
  representative of each province.

  - **Region:** The region codes which are going to be used within source code
  - **Region_name:** The main name of the regions

* **Years:** Including all the modelling years within the time horizon of the model with the following columns. The operation mode of the model accepts only one year, while
  the planning mode acceptes multiple years with both short-term and long-term horizons.

  - **Years:** The year codes
  - **Years_name:**. The main name of the years


* **Technologies_glob:** Including all the technologies within all the regions of the model with following columns

  - **Technology:** The technology codes
  - **Tech_name:** The real name of the technologies
  - **Tech_category:** The cargory of technologies


* **Carriers_glob:** Including all the carriers within all the regions of the model with the follwowing columns:

  - **Carrier:** The carrier codes
  - **Carr_name:** The real name of the carriers
  - **Carr_type:** The carrier types


* **Timesteps:** Including all the time slices within each year of the model with the follwowing columns. The temporal resolution is completely arbitary and can differ based on the user goal,
  from seasonal timeslices down to hourly resolutions in both the operation and planning modes.

  - **Timeslice:** The ordered number of the timeslices
  - **Timeslice_name:** The names of the timeslices
  - **Timeslice_fraction:** The fraction each the timeslice to the length of the whole year


When the :guilabel:`&global.xlsx` is prepared, for every single region, an excel file is required. The name of the regional files must be exactly similar to the region
codes given in the :guilabel:`&global.xlsx` file. For example if "reg1" is given as the region code of the first region, the set file for this region
should be named as :guilabel:`&reg1.xlsx`.

For every single regional file, it is required to provide the following information:

* **Technologies:** Including all the technologies within the RES of the specified region with following columns:

  - **Technology:** The technology codes
  - **Tech_name:** The real name of the technologies
  - **Tech_category:** The cargory of technologies


* **Carriers:** Including all the carriers within the RES of the specified region with the follwowing columns:

  - **Carrier:** The carrier codes
  - **Carr_name:** The real name of the carriers
  - **Carr_type:** The carrier types


* **Carrier_input:** Including the input carriers of different technologies with the follwowing columns:

  - **Technology:** The technology codes
  - **Carrier_in:** The input carrier


* **Carrier_output:** Including the output carriers of different technologies with the follwowing columns:

  - **Technology:** The technology codes
  - **Carrier_out:** The output carrier


.. note::

  If there are similar technologies in various regions, their names must be identical in different regional set files 
  and therefore, only one name as the representative of that technology in all the regions must be included in the “Technologies_glob” in the global set file.
  For example, if there is Hydropower plant in some of the considered locations within the geographical coverage of the model, one single name such as “Hydro PP” 
  must be considered in all the regional set files and this name should be brought only once in the “global” set file.

.. note::

  * Supply technologies have no Carrier_in and accept only Carrier_out
  * Demand technologies have no Carrier_out and accpet only Carrier_in
  * Conversion technologies accept only one Carrier_in and one Carrier_out
  * Conversion_plus technologies accept multiple Carrier_in and multiple Carrier_out


When these excel files are ready, you can start creating your **Model** and debuging possile mistakes in the definition of sets.
In order to initialize the model, you need to import the :guilabel:`&Model` class. Two inputs must be passed to the Model class for initializing the model:

#. path to the folder where the sets files are located 
#. the mode of the model:

  * **Operation:** for the operational analysis in one year
  * **Planning:** for continuous capacity deployment analysis

.. code-block:: python

  from hypatia import Model

  model = Model(
    path= 'path/to/sets/folder',
    mode= 'Planning'
  )

In order to have a rapid look on the model sets, you can print the model:

.. code-block:: python

  print(model)

.. note::
  Planning mode is only implementable when the time horizon is just one year.

When the sets are parsed successfully, the nexts step is to define the parameters for the model. Similar to the sets, parameters should be prepared in a set of excel files. The number
of the parameter files which can be created by the model is "n+2" where "n" is the number of the given regions. These files are named as follows:

* **parameters_connections.xlsx:** If a multi-node model model application is applied
* **parameters_global.xlsx:** If a nulti-node model application is applied
* **paramaters_{region_code}.xlsx:** For each region a parameter file will be created. These files are named based on the region codes that are given in the :guilabel:`&global.xlsx` set file.

Each parameter file includes different sheets for different data. As an example, the following table includes different sheets the regional parameter files.

.. list-table:: Parameters
   :widths: 20 25 15 20 20
   :header-rows: 1

   * - Group
     - Sheet Name
     - Description
     - Unit
     - Time dimension
     - Mode
   * - Economic
     - INV
     - Specific investment cost per unit of new installed capacity of each technology
     - Currency / Capacity unit
     - Modelling years
     - Planning
   * - Economic
     - F_OM
     - Specific fixed operation and maintenance cost per unit of total installed capacity of each technology
     - Currency / Capacity unit
     - Modelling years
     - Planning/Operational
   * - Economic
     - V_OM
     - Specific variable operation and maintenance cost per unit of production of each technology
     - Currency / Production unit
     - Modelling years
     - Planning/Operational
   * - Economic
     - Decom_cost
     - Specific decomissioning cost per unit of dismantled capacity of each technology
     - Currency / Capacity unit
     - Modelling years
     - Planning
   * - Economic
     - Investment_taxsub
     - 
     -
     -
   * - Economic
     - Fix_taxsub
   * - Economic
     - Carbon_tax
     - Specific tax on emission
     - Policy/Cost
     - Time horizon
     - Planning/Operational
   * - Fix_taxsub
     - Tax or subsidy on fix costs
     - Policy/Cost
     - Time horizon
     - Planning/Operational
   * - Residual_capacity
     - Residual capacity
     - Calibration
     - Time horizon
     - Planning/Operational
   * - Max_production
     - Maximum yearly production
     - Constraint
     - Time horizon
     - Planning/Operational
   * - Min_production
     - Minimum yearly production
     - Constraint
     - Time horizon
     - Planning/Operational
   * - Capacity_factor_tech
     - Technology capacity factor
     - Technical
     - Time horizon
     - Planning/Operational
   * - Tech_efficiency
     - Technology efficiency
     - Technical
     - Time horizon
     - Planning/Operational
   * - Specific_emission
     - Technology activity specific emission
     - Technical
     - Time horizon
     - Planning/Operational
   * - AnnualProd_perunit_capacity
     - Capacity to activity conversion
     - Technical
     - [-]
     - Planning/Operational
   * - Emission_cap_annual
     - Annual emission production budget
     - Policy
     - Time horizon
     - Planning/Operational
   * - Demand
     - Carrier deamnd for the technologies
     - Demand
     - Time horizon * Timeslice
     - Planning/Operational
   * - capacity_factor_resource
     - Resource capacity factor of technologies
     - Availability
     - Time horizon * Timeslice
     - Planning/Operational
   * - carrier_ratio_in
     - The ratio of carriers input for conversion_plus
     - Technical
     - Time horizon * Timeslice
     - Planning/Operational
   * - carrier_ratio_out
     - The ratio of carriers output for conversion_plus
     - Technical
     - Time horizon * Timeslice
     - Planning/Operational

.. note::
  Please refer to the example gallery for a better understanding of the structure of both the set and parameter files.


Since the parameter excel files are supposed to follow strict format and it is not easy to create all the sheets, you may use :guilabel:`&create_data_excels` function to automatically gerneate all the excel files.
Then, you can fill the excel files accordingly. For example, to save all the excel files in a directory called 'parameters':

.. code-block:: python

  model.create_data_excels(
    path = 'parameters'
  )

When the files are filled, you can parse the data to the model by specifing the directory of the folder containing the filled excel files:

.. code-block:: python

  model.read_input_data(
    path = 'parameters'
  )

Running a model
================
When the inputs of the model are correctly parsed to the model, you can run the model with specifying a couple of parameters:

.. code-block:: python

  model.run(
    solver = 'solver that you prefer'
  )

If model finds an optimum solution, you can have access to the results through :guilabel:`&results` attribute. For saving the results to your computer, use :guilabel:`&to_csv` function:

.. code-block:: python

  model.to_csv(
    path = 'path/to/directory'
  )

