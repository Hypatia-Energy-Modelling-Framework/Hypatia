"""
This module contains the functions for handling the example load
and example download.
"""

from hypatia.core.main import Model
from hypatia.analysis.plots import Plotter
import os
import shutil


path = os.path.abspath(os.path.join(os.path.dirname(__file__),))

DESCRIPTION = {
    "Planning": "Utopia Single Node Planning Model with Weekend/Weekdays and Day/Night resolution",
    "Operation": "Utopia Two Node Operation Model with hourly resolution",
}


def load_example(example):
    """Loads an example of mario.Database

    Parameters
    -----------
    example: str
        hypatia examples: ['Planning','Operation']

    Returns
    -------
    hypatia.Model

    Example
    --------
    .. code-block:: python

        from hypatia import load_examples

        model = load_examples('Planning')

        # check the configuration of the example model
        print(model)

        # There is a short descriotion about the example
        print(model.description)

        # you can run the model and see the results
        model.run(solver='gurobi',verbose=True)

        # To load the plots object
        plots = model.load_plots()
    """
    example = example.title()
    examples = ["Planning", "Operation"]
    if example not in examples:
        raise ValueError(f"Acceptable examples are {examples}")

    model = Model(path=f"{path}/{example}/sets", mode=example)
    model.read_input_data(path=f"{path}/{example}/parameters")
    model.description = DESCRIPTION[example]

    config_path = f"{path}/{example}/config.xlsx"
    hourly = True if example == "Operation" else False
    model.load_plots = lambda: Plotter(model, config_path, hourly)

    return model


def download_example(example, destination_path):
    """ Copies the model files from the site-packages to a given path

    Parameters
    -----------
    example : str
        Defines the embedded example to copy. Options are ['Planning','Operation']
    destination_path : str
        The path to copy the model files.
    """
    example = example.title()
    examples = ["Planning", "Operation"]
    if example not in examples:
        raise ValueError(f"Acceptable examples are {examples}")

    shutil.copytree(src=f"{path}/{example}", dst=destination_path)
