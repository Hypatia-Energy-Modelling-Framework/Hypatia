# -*- coding: utf-8 -*-
"""
The module contains the Error and Exception handling classes
"""


class WrongTableName(Exception):
    """Raises when the set tables have a wrong name
    """

    pass


class WrongSheetName(Exception):
    """Raises when sheet names in the excel files are wrong
    """

    pass


class WrongIndex(Exception):
    """Raises when excel files have wrong indexing
    """

    pass


class NanValues(Exception):
    """Raises when nan values exists in excel sheets
    """

    pass


class WrongTechCategory(Exception):
    """Raises when a tech in set files has not a correct caregory
    """

    pass


class WrongCarrierType(Exception):
    """Raises when a carrier in set files has not a correct type
    """

    pass


class WrongMappingData(Exception):
    """Raises when a technology or carrier in the carrier_input and carrier_output
    does not exists among the predefined technologies and carriers
    """

    pass


class WrongMappingTech(Exception):
    """Raises when the supply technologies are included in carrier input table
    or demand technologies are included in the carrier output table
    """

    pass


class WrongInputMode(Exception):
    """Raises when the mode of the model is not correct
    """

    pass


class DataNotImported(Exception):
    """Raises when solve method is called but data are not imported
    """

    pass


class ResultOverWrite(Exception):
    """Raises when results already exists but solve emthod is called again"""

    pass


class SolverNotFound(Exception):
    """Raises when a solver does not exists"""

    pass


class WrongNumberOfYears(Exception):
    """Raises when the mode of the model does not correspond with number of years
    """

    pass
