#######################################
Download and Installation
#######################################

Requirements
============
To run hyptia software, you need to have a couple of things on your machine:

* Python programming language, version 3.7 or higher
* A number of Python adds-on libraries
* A solver that is acceptable for hypatia domain-specific language
* hypatia software

Installing Python
------------------
There are many options to install python software and manage the packages but we recommend
. Conda is an open source pakcage manager which
can install hypatia and its depencies in an easy and user friendly way,

After `downloading and installing "Anacond Distribution" <https://www.anaconda.com/products/individual>`_, you need a python
IDE to run your codes. If it is your first time, working with Python, we strongly suggest
`Spyder <https://www.spyder-ide.org/>`_, which is free and open source scientific enviroment written in Python for
Python, and designed by and for scientisits, engineers, and data analysts.

Python module requirements
---------------------------
Installing hypatia software, will install minimum depencies automatically. Some of the key packages that hypatia relies on are:

#. `Pandas <https://pandas.pydata.org/>`_
#. `Numpy <https://numpy.org/>`_
#. `Plotly <https://plotly.com/>`_
#. `Cvxpy <https://pypi.org/project/cvxpy/>`_ (domain-specific language)

Solvers
--------
**cvxpy** supports multiple open source solvers such as:

* `CBC <https://projects.coin-or.org/Cbc>`_
* `GLPK <https://www.gnu.org/software/glpk/>`_
* `OSQP <https://osqp.org/>`_
* `ECOS <https://www.embotech.com/ECOS>`_
* `cvxopt <http://cvxopt.org/>`_
* `SCS <https://github.com/cvxgrp/scs>`_

and some commercial solvers:

* `CPLEX <https://www.ibm.com/products/category/business/commerce>`_
* `GUROBI <https://www.gurobi.com/>`_

by defualt OSQP, ECOS, cvxopt and GLPK will be installed with Hypatia.

.. note::

    Depending on the complexities of the model, open solvers may fail in solving process.


Recommended installation method
===============================

There are different ways to install hypatia software on your machine:

**Installing with pip**

In case that you are using pip, it is suggested to create a new environment to avoid conflicts of the other packages.
To create a new environment, you should use *Anaconda Prompt*:

.. code-block:: bash

    conda create -n hypatia python=3.8

If you create a new environment for hypatia, to use it, you need to activate the mario environment each time by writing
the following line in *Anaconda Prompt*:

.. code-block:: bash

    conda activate hypatia

After activateing the environment, you can use *pip* to install hypatia as follow:

.. code-block:: bash

    pip install hypatia


**Installing with conda**



**Installing manually**




