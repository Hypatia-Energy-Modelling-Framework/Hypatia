########################################
Building and Running a Model
########################################


Building a model
==================

Building a model in hypatia is very simple and includes three main steps:

#. Defining the **Reference Energy System (RES)**
#. Filling the parameters of the model through a sets of excel file that can be generated automatically by the model
#. Running the model after giving the parameters

In order to create a RES, you just need hypatia terminology to define the correct type of technology or energy carrier.
The RES will be defined using a couple of excel files:

* global.xlsx which contains the information about:

    * Time horizon
    * Time resolution
    * Golabl technologies (within the whole spatial resolution) and their type
    * Global energy carriers and their type
    * Nodes or regions of the model

* a couple of other excel files defined by the name of region that should contain informatio about:

    * Available technologies in the region
    * Available energy carriers in the region
    * The carrier in and carrier out of any single technology in the region



Time Horizon
-------------
time horizon in hypatia defines the number of **Years** to be modeled. Every year in the time horizon is a point that model make the decisions on the
expansion of the technologies. The acceptable time step for hypatia is one year.

Time resolution
----------------
hypatia accpets any kind of user specified time resolution from yearly, seasonal, day and night, to hourly time resultion. The time resolution will be defined by defining the timeslices and the fraction
of every timeslice in terms of number of hours in a year.


Technology Definiton
---------------------
hypatia uses a technology classification inspired by `Calliope <https://calliope.readthedocs.io/en/stable/index.html>`_ as follow:

.. list-table:: hypatia technology type terminology
   :widths: 25 50
   :header-rows: 1

   * - Technoloy Type
     - Definition
   * - Supply
     - Supplies an energy carrier without consuming any energy carrier within the RES
   * - Demand
     - Only consumes an energy carrier in the RES
   * - Transmission
     - Transmit an energy carrier from the production point to the consumption point (local and cross border transmission)
   * - Conversion
     - Supplies an energy carrier by converting (consuming) another energy carrier
   * - Conversion_plus
     - Supplies one/multiple energy carrier/s by converting (consuming) an/multiple energy carrier/s (such as CHP plants)

Carriers Definiton
-------------------
besides technology classifications, hypatia also considers different kinds of energy carriers as follow:

.. list-table:: hypatia carrier type terminology
   :widths: 25 50
   :header-rows: 1

   * - Carrier Type
     - Definition
   * - Resource
     - The energy source extracted from nature and not processed such as sun or raw oil
   * - Intermediate
     - An energy carrier that can be consumed by **non-Demand** technologies
   * - Demand
     - An energy carrier that can be consumed by **Demand** technologies

Regions
--------
Every single region represents a site that can have multiple specified technologies and carriers of any kind. The regions can be connected through the transmission technologies for
trading different carriers.


Definiton of sets
------------------
The sets of the model will be defined through a couple of excel files and by using excel tables. The first excel file that defines global sets, should be named :guilabel:`&global.xlsx`.
Within this file, following information should be defined:

* Regions
* Years
* Technologies and Technology Category
* Carriers and Carrier Type
* Timeslices and Timeslice Fraction

When the :guilabel:`&global.xlsx` is prepared, for every single **Region**, a single excel file is required which has the same name of the region. For example, if model has a region called **utopia**,
the file should be named :guilabel:`&utopia.xlsx`.

For every single region, there is the need of defining following information:

* Available technologies in the region
* Available carriers in the region
* Specifing the **Carrier_in** and **Carrier_out** for the technologies.

.. note::

  * Supply technologies have no Carrier_in and accept only Carrier_out
  * Demand technologies have no Carrier_out and accpet only Carrier_in
  * Conversion technologies accept only one Carrier_in and one Carrier_out
  * Conversion_plus technologies accept multiple Carrier_in and multiple Carrier_out

When these excel files are ready, you can start creating your **Model** and debuging possile mistakes in the definition of sets.
In order to initialize the model, you need to import the :guilabel:`&Model` class. For initializing the model, two inputs to the Model
class are needed:

#. path to the folder which sets files are
#. the mode of the model:

  * **Operational:** for operational analysis just for a single year
  * **Planning:** for continues capacity expansion analysis

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

When the sets are parsed successfully, the nexts step is to define the parameters for the model. Like sets, parameters should be prepared in a set of excel files. For every single region,
the excle file should be called in a specific way. Assuming that model has one region called **utopia**,
the file should be named :guilabel:`&parameters_utopia.xlsx`. Depending on the mode of the mode, different input parameters maybe required. Every parameter of a region should be specified in
different sheets of the excel file. Following table represents different sheet names with a short description.

.. list-table:: Parameters
   :widths: 20 25 15 20 20
   :header-rows: 1

   * - Sheet name
     - Description
     - Category
     - Time dimension
     - Mode
   * - INV
     - Investment cost
     - Costs
     - Time horizon
     - Planning
   * - F_OM
     - Fix O&M
     - Costs
     - Time horizon
     - Planning/Operational
   * - V_OM
     - Variable O&M
     - Costs
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
   * - Carbon_tax
     - Specific tax on emission
     - Policy/Cost
     - Time horizon
     - Planning/Operational
   * - Fix_taxsub
     - Tax or subsidy on fix costs
     - Policy/Cost
     - Time horizon
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


As the excel files are supposed to follow strict format and is not easy to create all the sheets, you may use :guilabel:`&create_data_excels` function to automatically gerneate all the excel files.
Then, you can fill the excel files accordingly. For example, to save all the excel files in a directory called 'parameters':

.. code-block:: python

  model.create_data_excels(
    path = 'parameters'
  )

In case that the model is multi region, an extra file will be needed (and will be created by the function) called :guilabel:`&parameters_connections.xlsx` which is specified for shaping the
connections between the regions.

When the files are filled, you can parse the data to the model by specifing the directory of the folder containing the excel files:

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

