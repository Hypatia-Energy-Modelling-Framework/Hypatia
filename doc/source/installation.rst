#######################################
Download and Installation
#######################################

Requirements
============
To run the hyptia software, you need to have a couple of things on your machine:

* Python programming language, version 3.7 or higher
* A number of Python adds-on libraries
* A solver that is acceptable for hypatia domain-specific language
* Hypatia software

Installing Python
------------------
There are many options to install Python and manage its packages but we recommend to
use the free conda package manager that can install hypatia and its depencies in an easy and user friendly way.

After `downloading and installing "Anaconda Distribution" <https://www.anaconda.com/products/individual>`_, you need a python
IDE to run your codes. If it is your first time, working with Python, we strongly suggest
`Spyder <https://www.spyder-ide.org/>`_, which is a free and open source scientific enviroment written in Python for
Python, and designed by and for scientisits, engineers, and data analysts.

Python module requirements
---------------------------
By installing the hypatia software, you will install minimum depencies automatically. Some of the key packages that hypatia relies on are:

#. `Pandas <https://pandas.pydata.org/>`_
#. `Numpy <https://numpy.org/>`_
#. `Plotly <https://plotly.com/>`_
#. `Cvxpy <https://pypi.org/project/cvxpy/>`_ 

.. note::

   The CVXPY library that is the domain specific optimization language used to write the Hypatia core code will not be installed
   automatically after installing the hypatia software. Therefore, it is required to install it separately as it is demonstrated in the following.

Solvers
--------
**cvxpy** supports multiple open source solvers such as:

* `CBC <https://projects.coin-or.org/Cbc>`_
* `GLPK <https://www.gnu.org/software/glpk/>`_
* `OSQP <https://osqp.org/>`_
* `ECOS <https://www.embotech.com/ECOS>`_
* `CVXOPT <http://cvxopt.org/>`_
* `SCS <https://github.com/cvxgrp/scs>`_
* `Scipy <https://scipy.org>`_

and some commercial solvers:

* `CPLEX <https://www.ibm.com/products/category/business/commerce>`_
* `GUROBI <https://www.gurobi.com/>`_

Some solvers including OSQP, ECOS, cvxopt, GLPK, SCS and Scipy will be installed with Hypatia, automatically, so for installing the other solvers, you need to
refer to the solver website for the installation instruction.

.. note::

    Depending on the complexities of the model, some solvers may fail in solving process.


Recommended installation method
===============================

There are different ways to install the hypatia software on your machine. The fastest one is through pip:

**Installing with pip**

If you are using pip, it is suggested to create a new environment to avoid possible conflicts with the other packages.
To create a new environment, you should use *Anaconda Prompt*:

.. code-block:: bash

    conda create -n hypatia python=3.8

If you create a new environment for hypatia, you need to activate the environment each time you want to use it, by writing
the following line in *Anaconda Prompt*:

.. code-block:: bash

    conda activate hypatia

After activating the environment, you first need to install **CVXPY** using **conda**:

.. code-block:: bash

    conda install -c conda-forge cvxpy

Then you can use **pip** to install the hypatia software:

.. code-block:: bash

    pip install hypatia-py






