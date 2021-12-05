# -*- coding: utf-8 -*-
"""
Hypatia: An Operation and Planning Energy System Modelling Framework
=============================================================================

Hypatia is an open source modelling framework written in Python that provides
a technology-rich basis for optimizing both the operation and planning mode of
the energy systems in short-term and long-term time horizons. Hypatia is able
to analyze various energy transition scnerios based on different policies such
as coal phase out, carbon taxes, renewable incetives and other national and
international pledges for the possible future energy systems.

Hypatia is a sector-coupled energy system optimization model that covers long-term
capacity expansion planning with user specified intra-year resolution.

Hypatia optimization core is written in CVXPY, which its strucuture gives the
opportunity to have a more transparent and understandable core. CVXPY supports
vectorial matehmatical operations that fasten the model loading and generation
faster with compare to many optimization libraries in Python. It covers a variaty
of open-source solvers such as:

    * CBC
    * GLPK
    * OSQP
    * ECOS
    * cvxopt
    * SCS

and some powerful commercial solvers such as:

    * GUROBI
    * CPLEX

Package dependencies:

    pandas
    numpy
    xlsxwriter
    plotly
    openpyxl
    IPython
    cvxpy
    cvxopt

:Authors: Negar Namazifard, Mohammad Amin Tahavori

:license: Apache 2.0
"""

from hypatia.core.main import Model
from hypatia.error_log import Exceptions
from hypatia.analysis.plots import Plotter
from hypatia.examples.load_examples import load_example, download_example
from hypatia.version import __version__
