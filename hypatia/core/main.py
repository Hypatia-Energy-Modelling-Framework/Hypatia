# -*- coding: utf-8 -*-
"""
Hypatia interface module. Contains the Model class with all
the methods needed to create,solve and save the results of a hypatia
model.
"""
from cvxpy import installed_solvers
from hypatia.error_log.Exceptions import (
    WrongInputMode,
    DataNotImported,
    ResultOverWrite,
    SolverNotFound,
)

from hypatia.backend.StrData import ReadSets
from hypatia.backend.Build import BuildModel
from copy import deepcopy
from hypatia.analysis.postprocessing import (
    set_DataFrame,
    dict_to_csv,
)
import os
import pandas as pd

import logging

logger = logging.getLogger(__name__)


class Model:

    """
    A Hypatia Model
    """

    def __init__(self, path, mode, name="unknown"):

        """Initializes a Hypatia model by passing the optimization mode and
        the path of the structural input files

        Parameters
        ----------
        path : str
            path defines the directory where model set files are located.
            model sets are including regions, modelling years, timeslices,
            technologies, carriers and regional mappings.

        mode : str
            Defines the mode of the model. Acceptable values are :

                * 'Planning'
                * 'Operation'

        name : str (Optional)
            Defines the name of the model.
        """

        self._StrData = ReadSets(path=path, mode=mode,)

        self.name = name

    def create_data_excels(self, path, force_rewrite=False):

        """Writes the parameter excel files with the default values and
        required indexing by passing an arbitary path

        .. note::

            The input data files are including regional parameter files and
            global and connections parameter files in case of multi-node model

        Parameters
        ----------
        path : str
            path defines the directory where model parameter files are going
            to be witten. It can be different from the path where set files
            are located

        force_rewrite : boolean
            to avoid over writing the parameters, this will stop the code if
            the same file already exists. In case, you need to over-write,
            force_rewrite = True will do it
        """
        if os.path.exists(path):
            if not force_rewrite:
                raise ResultOverWrite(
                    f"Folder {path} already exists. To over write"
                    f" the parameter files, use force_rewrite=True."
                )
            else:
                os.rmdir(path)

        os.mkdir(path)
        self._StrData._write_input_excel(path)

    def read_input_data(self, path):

        """Reades the filled input data excel files by passing the path
        where they are located

        Parameters
        -------
        path : str
            path defines the directory where the filled input parameter files
            are located. It can be different from the path where the parameter
            files with default values were written

        """

        self._StrData._read_data(path)

    def run(self, solver, verbosity=True, force_rewrite=False, **kwargs):

        """
        Run the model by passing the solver, verbosity and force_rewrite.

        .. note::

            The passed solver must be in the installed solvers package of the DSL
            (CVXPY).

        Parameters
        ---------
        solver : str
            Solver indicates for kind of solver to be used.

        verbosity : Boolean
            Verbosity overrides the default of hiding solver output

        force_rewrite : boolean
            If the force_rewrite is True, any existing results will
            be overwritten and the previous results will be saved
            in a back-up file.

        kwargs : Optional
            solver specific options. for more information refer to `cvxpy documentation <https://www.cvxpy.org/api_reference/cvxpy.problems.html?highlight=solve#cvxpy.problems.problem.Problem.solve>`_

        """

        # checks if the input parameters are imported to the model
        if not hasattr(self._StrData, "data"):

            raise DataNotImported(
                "No data is imported to the model. Use " "'read_input_data' function."
            )

        # checks if the model is already solved when force_rewrite is false
        # and takes a backup of previous results if force_rewrite is true
        if hasattr(self, "results"):

            if not force_rewrite:
                raise ResultOverWrite(
                    "Model is already solved."
                    "To overwrite the results change "
                    "'force_rewrite'= True"
                )

            self.backup_results = deepcopy(self.results)

            delattr(self, "results")

        # checks if the given solver is in the installed solver package
        if solver.upper() not in installed_solvers():

            raise SolverNotFound(
                f"Installed solvers on your system are {installed_solvers()}"
            )

        model = BuildModel(sets=self._StrData)

        results = model._solve(verbosity=verbosity, solver=solver.upper(), **kwargs)
        self.check = results
        if results is not None:

            results = set_DataFrame(
                results=results,
                regions=self._StrData.regions,
                years=self._StrData.main_years,
                time_fraction=self._StrData.time_steps,
                glob_mapping=self._StrData.glob_mapping,
                technologies=self._StrData.Technologies,
                mode=self._StrData.mode,
            )

            self.results = results

    def to_csv(self, path, force_rewrite=False):
        """Exports the results of the model to csv files with nested folders

        Parameters
        ----------
        path : str
            Defines the path to th 'folder' which all the results will be
            created.
        force_rewrite : boolean
            if False, will stop the code in case the file already exists,
            if True, will delete the file if alreadey exists and create a new one
        """

        if not hasattr(self, "results"):
            raise WrongInputMode("model has not any results")

        if os.path.exists(path):
            if not force_rewrite:
                raise ResultOverWrite(
                    f"Folder {path} already exists. To over write"
                    f" the results, use force_rewrite=True."
                )
        else:
            os.mkdir(path)

        dict_to_csv(self.results, path)

    def create_config_file(self, path):
        """Creates a config excel file for plots

        Parameters
        ----------
        path : str
            defines the path and the name of the excel file to be created.
        """

        techs_property = {"tech_name": list(self._StrData.glob_mapping["Technologies_glob"]["Tech_name"]),
                "tech_group": '',
                "tech_color": '',
                "tech_cap_unit": list(self._StrData.glob_mapping["Technologies_glob"]["Tech_cap_unit"]),
                "tech_production_unit": list(self._StrData.glob_mapping["Technologies_glob"]["Tech_act_unit"]),}

        techs_sheet = pd.DataFrame(techs_property,
            index=self._StrData.glob_mapping["Technologies_glob"]["Technology"],
        )

        fuels_property = {"fuel_name": list(self._StrData.glob_mapping["Carriers_glob"]["Carr_name"]),
                "fuel_group": '',
                "fuel_color": '',
                "fuel_unit": list(self._StrData.glob_mapping["Carriers_glob"]["Carr_unit"]),}

        fuels_sheet = pd.DataFrame(fuels_property,
            index=self._StrData.glob_mapping["Carriers_glob"]["Carrier"],
        )

        regions_property = {"region_name": list(self._StrData.glob_mapping["Regions"]["Region_name"]),
                "region_color": '',}

        regions_sheet = pd.DataFrame(regions_property,
            index=self._StrData.glob_mapping["Regions"]["Region"],
        )
        
        emissions_sheet = self._StrData.glob_mapping['Emissions'].set_index(['Emission'],inplace=False)


        with pd.ExcelWriter(path) as file:
            for sheet in [
                "techs_sheet",
                "fuels_sheet",
                "regions_sheet",
                "emissions_sheet",
            ]:
                eval(sheet).to_excel(file, sheet_name=sheet.split("_")[0].title())

    def __str__(self):
        to_print = (
            "name = {}\n"
            "mode = {}\n"
            "regions= {}\n"
            "techs= {}\n"
            "horizon= {}\n"
            "resolution= {}\n".format(
                self.name,
                self._StrData.mode,
                self._StrData.regions,
                self._StrData.Technologies,
                self._StrData.main_years,
                len(self._StrData.time_steps),
            )
        )

        return to_print

    def __repr__(self):
        return self.__str__()
