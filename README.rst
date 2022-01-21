
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    
.. image:: https://readthedocs.org/projects/hypatia-py/badge/?version=latest
    :target: https://hypatia-py.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
    
.. image:: https://raw.githubusercontent.com/SESAM-Polimi/MARIO/767d2c0e9e42ae0b6acf7c3a1cc379d7bcd367fa/doc/source/_static/images/polimi.svg
   :width: 200
   :align: right
   
.. image:: https://badges.gitter.im/Hypatia-py/community.svg
    :target: https://gitter.im/Hypatia-py/community?utm_source=share-link&utm_medium=link&utm_campaign=share-link
    :alt: Documentation Status

********
Hypatia
********
An Operation and Planning Energy System Modelling Framework


What is it
-----------
Hypatia is an open source modelling framework written in Python that provides
a technology-rich basis for optimizing both the operation and planning mode of
the energy systems in short-term and long-term time horizons. Hypatia is able
to analyze various energy transition scnerios based on different policies such
as coal phase out, carbon taxes, renewable incetives and other national and
international pledges for the possible future energy systems.

Quickstart
----------
There are different ways to install hypatia software on your machine. The fastest one is through pip:

In case that you are using pip, it is suggested to create a new environment to avoid conflicts of the other packages.
To create a new environment, you should use *Anaconda Prompt*:

.. code-block:: bash

    conda create -n hypatia python=3.8

If you create a new environment for hypatia, you need to activate the environment each time you want to use it, by writing
the following line in *Anaconda Prompt*:

.. code-block:: bash

    conda activate hypatia

After activating the environment, you need to install **CVXPY**:

.. code-block:: bash

    conda install -c conda-forge cvxpy 
    
Then, you can use *pip* to install hypatia as follow:

.. code-block:: bash

    pip install hypatia-py

Most of the open source solvers that are supported by CVXPY (the optimization library used in Hypatia), will be installed
automatically with the software. For the commercial solvers, you should follow the specific installation methods. 
When Hypatia is installed, you can strat to use the embedded examples as a quick start:

.. code-block:: python

    from hypatia import load_example

    # Loading the planning example
    planning = load_example('Planning')

    # Loading the Operation example
    operation = load_example('Operation')

    # See the configuration of systems
    print(planning)
    print(operation)

    # see the description of systems
    print(planning.description)
    print(operation.description)

    # Running models
    planning.run(solver='glpk')

    # Save the results
    planning.to_csv(path= '../save/directory')

If you want to see the structure of inputs and how the examples are built, you can download the data files to a specific place in your machine:

.. code-block:: python

    from hypatia import download_example

    # Downloading the Planning example
    download_example(example='Planning', destination_path='Where/To/Save')


Python module requirements
--------------------------
Some of the key packages that Hypatia relies on are:

#. `Pandas <https://pandas.pydata.org/>`_
#. `Numpy <https://numpy.org/>`_
#. `Plotly <https://plotly.com/>`_
#. `Cvxpy <https://pypi.org/project/cvxpy/>`_ (domain-specific language)

Hypatia supports different **Open Source** and **Commercial** solvers like:

* `CBC <https://projects.coin-or.org/Cbc>`_
* `GLPK <https://www.gnu.org/software/glpk/>`_
* `OSQP <https://osqp.org/>`_
* `ECOS <https://www.embotech.com/ECOS>`_
* `CVXOPT <http://cvxopt.org/>`_
* `SCS <https://github.com/cvxgrp/scs>`_
* `CPLEX <https://www.ibm.com/products/category/business/commerce>`_
* `GUROBI <https://www.gurobi.com/>`_


.. note::
   * This project is under active development.


License
-------

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
    :target: https://www.apache.org/licenses/


This work is licensed under `Apache 2.0 <https://www.apache.org/licenses/>`_

