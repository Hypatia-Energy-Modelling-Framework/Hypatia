
.. image:: https://raw.githubusercontent.com/SESAM-Polimi/MARIO/767d2c0e9e42ae0b6acf7c3a1cc379d7bcd367fa/doc/source/_static/images/polimi.svg
   :width: 200
   :align: right
   
#######################################
Introduction
#######################################
What is Hypatia
=========================================
Hypatia is an energy system modelling framework written in the objective oriented
Python programming language. Contrary to most of the Python-based open-source energy and power
system modelling frameworks that are using `Pyomo <https://pyomo.readthedocs.io/en/stable/>`_ for 
solving the optimization problem, Hypatia is based on `CVXPY <https://www.cvxpy.org/>`_ Domain-Specific Language 
developed by [Diamond2016]_ . Hypatia can optimize both the hourly dispatch 
and the annual capacity deployments of the energy system. Its final objective is 
to minimize the total discounted cost of the system by considering all the required cost components 
in each of its optimization modes. In summery, Hypatia is designed with the following main goals:

* Allow easy interaction with the model code by using excel-based input data

* Formulated to cover both operation and dynamic investment decisions

* Provide the possibility to consider the investment annuities in its planning mode
  based on the given economic lifetime and interest rate of each technology

* Allow to model various categories of technologies such as supply, conversion,
  transmission and storage.

* Able to consider the synergies among different sectors of the energy system including
  power, heat, transport, clean fuel (Hydrogen) and the others.

* Designed to follow both the single-node and multi-node approach at will by the user.
  Each node in Hypatia can be representative of a broad spectrum of spatial resolutions
  starting from small-scale applications to the national and continental applications.

* Allow to model the bilateral trade among any pairs of nodes through modelling the
  inter-regional transmission links for all the represented energy carriers within the Reference Energy System

* Able to adopt arbitary resolutions in time for each modelling year,
  allowing to consider the full hourly variability of both demand and supply sides.

* Have a fully transparent and open-source code, flexible to any possible future
  modification and integration

Why it is developed
=========================================
Hypatia is inspired by the other existing energy system optimization models 
particulary `OSeMOSYS <http://www.osemosys.org/>`_ by [Howells2011]_, 
`Calliope <https://calliope.readthedocs.io/en/stable/user/introduction.html>`_ by [Pfenninger-Pickering2018]_
and `TIMES <https://iea-etsap.org/index.php/documentation>`_ by [Loulou2005]_.
It is designed to compelete the path of these frameworks by addressing the main 
challenges of the modern energy system modelling frameworks that are shortly explained in the following:

* **Dynamic annual investments on the energy system:** With the aim of
  exploring the possible evolution of the energy systems in the transition pathways,
  the energy modeling frameworks need to cover both the operation and planning modes by simulateneously 
  delivering the required dynamic annual capacity expansions and full hourly dispatch of different technologies within the energy systems. 
  However, most of the existing models with high temporal resolution are falling
  short of delivering all the required annual investments in the long-term horizons and just
  follow a snapshot approach for estimating the required new capacities to be installed for the future growths in the final demand.


* **Resolution in time:** On the other hand, most of the planning models are not computationally
  able to include fine temporal resolutions down to hourly timesteps within each modelling year
  of the time horizon. Therefore, they may deliver inaccurate results due to missing the full variability
  of the both demand and supply sides of the energy system.
  
* **Resolution in space:** The concept of spatial resolution contains not only the ability of
  representing multiple regions in different dimensions but also the possibility to model the 
  interconnections among various regions by modelling the inter-regional transmission links.
  
* **Sector coupling:** The interactions and synergies among different sectors of the energy system
  must be considered in the energy modelling frameworks by following a comprehensive technology definition
  similar to all the above mentioned models.
    
* **Transparency:** The concept of transparency and opennes has manifold aspects. The open science
  approach for an energy model is not only about publishing the governing structures and equations but also
  following several critieria such as:
  
  * Convenient access to source code, data and assumptions
  * Providing understanble input data structure not only for the experts but also for any potential user
  * Clear and modular core code
  * Flexible source code to any possible future modification and integration

Acknowledgement
=========================================

* The development of Hypatia was not possible without the kind attention and help of Professor
  `Emanuela Colombo <https://www4.ceda.polimi.it/manifesti/manifesti/controller/ricerche/RicercaPerDocentiPublic.do?EVN_DIDATTICA=evento&k_doc=44891&lang=EN&aa=2014&tab_ricerca=1>`_.
  We are fully grateful for having the chance to work under her supervison and would like to express our gratitude for her unwavering support.

* We would also like to acknowledge `Steve Dimond <https://stevediamond.github.io/WWW/>`_ for his kind support and guide that allows us to better understand and use CVXPY for this framework
    
License
========

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
    :target: https://www.apache.org/licenses/


This work is licensed under `Apache 2.0 <https://www.apache.org/licenses/>`_

References
=========================================
.. [Diamond2016] Diamond, S., & Boyd, S. (2016). CVXPY: A Python-embedded modeling language for convex optimization. The Journal of Machine Learning Research, 17(1), 2909-2913.
.. [Howells2011] Howells, M., Rogner, H., Strachan, N., Heaps, C., Huntington, H., Kypreos, S., ... & Roehrl, A. (2011). OSeMOSYS: the open source energy modeling system: an introduction to its ethos, structure and development. Energy Policy, 39(10), 5850-5870.
.. [Pfenninger-Pickering2018] Pfenninger, S., & Pickering, B. (2018). Calliope: a multi-scale energy systems modelling framework. Journal of Open Source Software, 3(29), 825.
.. [Loulou2005] Loulou, R., Remme, U., Kanudia, A., Lehtila, A., & Goldstein, G. (2005). Documentation for the times model part ii. Energy Technology Systems Analysis Programme.


