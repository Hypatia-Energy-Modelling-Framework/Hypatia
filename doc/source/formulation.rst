#######################################
Mathematical Formulation
#######################################
.. role:: raw-html(raw)
    :format: html

Objective function
===================
The objective function equation of the planning mode is the sum of all the regional
and cross-border transmission link costs discounted to the reference year.
While, in the operational mode, the objective function is just the sum of the
fixed and variable costs with their related taxes within the modeled year.

Planning mode
--------------
Total Objective Function
^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         min: Eq\_{obj} = \sum_{reg} Reg\_{obj}(reg) + Exchange\_{links}\_{obj} \;\;\;	\forall reg \in regions
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Regional Objective Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         Reg\_{obj}(reg) =
          \sum_{year} (1+Discount\_{rate}(year,reg))^{-year}
          \times \sum_{tech} \bigg[InvCost(reg,year,tech)+FixCost(reg,tech,year)+
          DecomCost(reg,tech,year)+VarCost(reg,tech,year)+FixTax(reg,tech,year)+InvTax(reg,tech,year)-
          InvSub(reg,tech,year)-FixSub(reg,tech,year)+
          CO2Cost(reg,tech,year)-InvSalvage(reg,tech,year)\bigg]
         \;\;\; \forall reg \in regions , \forall year \in years , \forall tech \in technologies
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Trades Objective Function
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         Exchange\_{links}\_{obj} =
         \sum_{year} (1+Discount_{rate}(year))^{-year}
         \times \sum_{link} \bigg[InvCost\_{link}(year,link)+
         FixCost\_{link}(year,link)+DecomCost\_{link}(year,link)+
         VarCost\_{link}(year,link)+FixTax\_{link}(year,link)+
         InvTax\_{link}(year,link)-InvSub\_{link}(year,link)-
         FixSub\_{link}(year,link)-InvSalvage\_{link}\bigg]
         \;\;\; \forall year \in years , \forall link \in links
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Operation mode
--------------
Total Objective Function
^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         min: Eq\_{obj} = \sum_{reg} Reg\_{obj}(reg) + Exchange\_{links}\_{obj}
         \forll reg \in regions
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Regional Objective Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         Reg\_{obj}(reg) = \sum_{tech}
         \bigg[FixCost(reg,tech)+
         VarCost(reg,tech)+FixTax(reg,tech)-
         FixSub(reg,tech)+CO2Cost(reg,tech)\bigg]
         \forall reg \in regions , \forall tech \in technologies
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Trades Objective Function
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         Exchange\_{links}\_{obj} = \sum_{link}
         \bigg[FixCost\_{link}(link)+VarCost\_{link}(link)+
         FixTax\_{link}(link)-FixSub\_{link}(link)\bigg]
         \forall link \in links
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Equations
==========

costs
------

calculating the components of the objective function including the investment,
fixed and variable operation and maintenance and decommissioning costs followed
by the related taxes considered for each unit of investment or fixed cost
of the technologies. Carbon taxes are also included to be applied for the
carbon-intensive technologies. Alongside the related costs of technologies,
some revenues are considered in the objective function with a negative sign.
These revenues are including subsidies that are applied to some technologies
based on the national policies and the salvage values.
The Hypatia model considers the economic life time of the technologies in the
investment cost calculation. Therefore, each required investment in a specific
year “y” is divided into a stream of annuities during several years
(from “y+1” to “y+ELIFE”) which is determined by the technology-specific
economic lifetime, depreciation rate and time value of money.

.. note::

   In Hypatia, the inter-regional links are modeled as technologies. Therefore all the below
   equations for calculating the objective function cost components and intermediate
   variables except all the taxes and subsidies have been correspondingly written for the links.


Investment Cost
^^^^^^^^^^^^^^^^^^^^^^^^^

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years:
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Inv\_{present}}(reg,tech,year) =
         \boldsymbol{NewCapcity}(reg,tech,year)
         \times INV(reg,tech,year)
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         Depreciation(reg,tech) = \frac{r(1+r)^n}{(1+r)^n-1}
         \text{where:} \; n = Economic\_{lifetime}(reg,tech) \;\;
         r = Interest\_{rate}(reg,tech)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Annuity}(reg,tech,year_k) =
         Depreciation(reg,tech) \times
         \boldsymbol{Inv\_{present}}(reg,tech,year)
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{InvCost}(reg,tech,y) =
         \sum_{year_k=year+1}^{year+Economic\_{lifetime}+1}
         (1+Discount\_{rate})^{year-year_k} \times \boldsymbol{annuity}(reg,tech,year_k)	\forall reg \in regions , \forall tech \in technologies , \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Investment Salvage Value
^^^^^^^^^^^^^^^^^^^^^^^^^

Fixed Cost
^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{FixCost}(reg,tech,year) =
         \boldsymbol{TotalCapacity}(reg,tech,year)
         \times F\_{OM}(reg,tech,year)	\forall reg \in regions ,
         \forall tech \in technologies , \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Taxes & Subsidies
^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies , \forall year \in years:

      \end{eqnarray}

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{InvTax}(reg,tech,year) = \boldsymbol{NewCapacity}(reg,tech,year) \times Investment\_{tax}(reg,tech,year) \times INV(reg,tech,year)
      \end{eqnarray}

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{InvSub}(reg,tech,year) = \boldsymbol{NewCapacity}(reg,tech,year) \times Investment\_{sub}(reg,tech,year) \times INV(reg,tech,year)
      \end{eqnarray}

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{FixTax}(reg,tech,year) = \boldsymbol{TotalCapacity}(reg,tech,year) \times Fix\_{tax}(reg,tech,year) \times F\_{OM}(reg,tech,year)
      \end{eqnarray}

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{FixSub}(reg,tech,year) = \boldsymbol{TotalCapacity}(reg,tech,year) \times Fix\_{sub}(reg,tech,year) \times F\_{OM}(reg,tech,year)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Decommissioning Cost
^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{DecomCost}(reg,tech,year) =
         \boldsymbol{DecomCap}(reg,tech,year)
         \times Decom\_{cost}(reg,tech,year)
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Variable Cost
^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{VarCost}(reg,tech,year) =
         \boldsymbol{Production\_{annual}}(reg,tech,year)
         \times V\_{OM}(reg,tech,year)	\forall reg \in regions ,
         \forall tech \in technologies , \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Carbon Tax
^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{CO2Cost}(reg,tech,year) =
         \boldsymbol{Production\_{annual}}(reg,tech,year)
         \times Specific\_{emission}(reg,tech,year)
         \times Carbon\_{tax}(reg,tech,year)	\forall reg
         \in regions , \forall tech \in technologies ,
         \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Capacity
----------

Accumulated New Installed Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Accumulated\_{NewCapacity}}(reg,tech,year) =
         \sum_{vintage_year} \boldsymbol{NewCapacity}(reg,tech,vintage_year)
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years
         if \; year - vintage\_{year} \leq Tech\_{lifetime}(reg,tech)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Total Installed Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{TotalCapacity}(reg,tech,year) =
         \boldsymbol{Accumulated\_{NewCapacity}}(reg,tech,year) +
         Residual\_{capacity}(reg,tech,year)	\forall reg \in regions ,
         \forall tech \in technologies , \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Decomissioned Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Calculates the annual decommissioning capacities based on the previously installed
new capacities in the vintage years of the horizon.

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{DecomCapacity}(reg,tech,y) =
         \sum_{vintage_year} \boldsymbol{NewCapacity}(reg,tech,vintage_year)
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years	if \; year - vintage\_{year}
         \geq Tech\_{lifetime}(reg,tech)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Emission
----------

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{CO2\_{equivalent}}(reg,tech,year) =
         \boldsymbol{Production\_{annual}}(reg,tech,year)
         \times Specific\_{emission}(reg,tech,year)
         \forall reg \in regions , \forall tech \in technologies ,
         \forall year \in years
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Constraints
=============

Energy balance
-----------------

Guarantees the balance between the supply and demand sides of the energy system.

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions ,
         \forall carr \in carriers ,
         \forall tech \in technologies ,
         \forall year \in years ,
         \forall ts \in timesteps
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{tech \notin tech\_{Demand}}
         \boldsymbol{Production}(reg,carr,tech,y,ts) +
         \sum_{REG} \boldsymbol{Imports}(reg,carr,REG,year,ts)
         \geq \sum_{tech \notin tech\_{Demand} \& tech\_{Supply}}
         \boldsymbol{Use}(reg,carr,tech,year,ts) + \sum_{REG}
         \boldsymbol{Exports}(reg,carr,REG,year,ts) +
         \sum_{tech \in tech\_{Demand}} \boldsymbol{Demand}(reg,carr,tech,year,ts)
      \end{eqnarray}

:raw-html:`<br />`

.. note::

   All the technologies within Hypatia have one input carrier or one output
   carrier except for the conversion plus techs where the production and use of
   each carrier must be calculated from the following eaquation:

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Production}(reg,carr,tech,y,ts) =
         \boldsymbol{Production\_{total}}(reg,tech,y,ts)
         \time Carrier\_{ratio}\_{output}(reg,carr,tech,y,ts)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Use}(reg,carr,tech,y,ts) =
         \boldsymbol{Use\_{total}}(reg,tech,y,ts)
         \time Carrier\_{ratio}\_{input}(reg,carr,tech,y,ts)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Trade balance
-----------------

Ensures that the amounts of imports and exports among any pair of
regions are completely balanced.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Imports}(reg,carr,REG,year,ts) =
         \boldsymbol{Exports}(REG,carr,reg,year,ts)
         \forall reg \& REG \in regions ,
         \forall carr \in carriers ,
         \forall year \in years ,
         \forall ts \in timesteps
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Resource & Technology Availability
-----------------------------------

Ensures that the production of each technology does not exceed its
available activity based technology capacity factor and resource capacity factor.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{carr} \boldsymbol{Production}(reg,carr,tech,year,ts)
         \leq \boldsymbol{TotalCapacity}(reg,tech,year)
         \times Resource\_{capacity}\_{factor}(reg,tech,year,ts)
         \times Annual\_{production}\_{per}\_{unitcapacity}(reg,tech)
         \times Timeslice\_{fraction}(ts)	\forall reg \in regions ,
         \forall carr \in carriers , \forall tech \in technologies,
         \forall year \in years , \forall ts \in timesteps
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{carr} \sum_{ts} \boldsymbol{Production}(reg,carr,tech,year,ts)
         \leq Capacity\_{factor}\_{}tech \times \sum_{ts}
         \bigg[\boldsymbol{TotalCapacity}(reg,tech,year)
         \times Resource\_{capacity}\_{factor}(reg,tech,year,ts)
         \times Annual\_{production}\_{per}\_{unitcapacity}(reg,tech)
         \times Timeslice\_{fraction}(ts)\bigg]	\forall reg \in regions ,
         \forall carr \in carriers , \forall tech \in technologies,
         \forall year \in years , \forall ts \in timesteps
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Capacity
----------

Maximum & Minimum Regional Total Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Maximum and minimum allowed annual total installed capacity for each
technology in each region.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions ,
         \forall tech \in technologies,
         \forall year \in years:
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{TotalCapacity}(reg,tech,year)
         \leq Max\_{totalcap}(reg,tech,year)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{TotalCapacity}(reg,tech,year)
         \geq Min\_{totalcap}(reg,tech,year)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Maximum & Minimum Regional New Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Maximum and minimum allowed annual new installed capacity for each technology in each region.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies, \forall year \in years:
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{NewCapacity}(reg,tech,year) \leq Max\_{newcap}(reg,tech,year)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{NewCapacity}(reg,tech,year) \geq Min\_{newcap}(reg,tech,year)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Maximum & Minimum Overall Total Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Maximum and minimum allowed annual aggregated total installed capacity for each technology over all the regions.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies, \forall year \in years:

      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \boldsymbol{TotalCapacity}(reg,tech,year) \leq Max\_{totalcap}\_{global}(tech,year)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \boldsymbol{TotalCapacity}(reg,tech,year) \geq Min\_{totalcap}\_{global}(tech,year)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Maximum & Minimum Overall New Capacity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Maximum and minimum allowed annual aggregated new installed capacity for each technology over all the regions.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies, \forall year \in years:

      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \boldsymbol{NewCapacity}(reg,tech,year) \leq Max\_{newcap}\_{global}(tech,year)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \boldsymbol{NewCapacity}(reg,tech,year) \geq Min\_{newcap}\_{global}(tech,year)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Activity
---------

Maximum & Minimum Regional Production
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Maximum and minimum allowed production of each technology in each region.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies, \forall year \in years:


      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Production\_{annual}}(reg,tech,year) \leq Max\_{production}(reg,tech,year)

      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Production\_{annual}}(reg,tech,year) \geq Min\_{production}(reg,tech,year)

      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Maximum & Minimum Overall Production
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Maximum and minimum aggregated production of each technology over all the regions.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \forall reg \in regions , \forall tech \in technologies, \forall year \in years:
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \boldsymbol{Production\_{annual}}(reg,tech,year) \leq Max\_{production}\_{global}(tech,year)
      \end{eqnarray}

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \boldsymbol{Production\_{annual}}(reg,tech,year) \geq Min\_{production}\_{global}(tech,year)
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Output to Input Activity Ratio
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \boldsymbol{Production}(reg,tech,year,ts) = Output\_{input}\_{act}\_{ratio}(reg,tech,year) \times \boldsymbol{Use}(reg,tech,year,ts) \forall reg \in regions , \forall tech \in technologies, \forall year \in years , \foral ts \in timesteps
      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

CO\ :sub:`2` Equivalent Emissions
----------------------------------

Regional Emission cap
^^^^^^^^^^^^^^^^^^^^^^

Ensures regional maximum allowed annual carbon emissions.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{tech} \boldsymbol{CO2\_{equivalent}}(reg,tech,year) \leq Emission\_{cap}\_{annual}(reg,year) \forall reg \in regions , \forall tech \in technologies, \forall year \in years

      \end{eqnarray}

:raw-html:`<br />`
:raw-html:`<br />`

Overall Emission cap
^^^^^^^^^^^^^^^^^^^^^^

Ensures global maximum allowed annual carbon emissions over all the regions.

:raw-html:`<br />`

.. container:: scrolling-wrapper

   .. math::
      :nowrap:

      \begin{eqnarray}
         \sum_{reg} \sum_{tech} \boldsymbol{CO2\_{equivalent}}(reg,tech,year) \leq Global\_{emission}\_{cap}\_{annual}(year) \forall reg \in regions , \forall tech \in technologies, \forall year \in years:
      \end{eqnarray}