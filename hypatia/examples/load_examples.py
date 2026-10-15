"""
Load or copy the example models shipped with Hypatia.

Every sub-folder of hypatia/examples with a "sets" folder is an example. Its
name decides how it is built: names starting with "Operation" are operation
models, the others planning models; names containing "UnMetDemand" allow unmet
demand (ensure_feasibility="Yes").
"""
import os
import shutil

from hypatia.core.main import Model
from hypatia.analysis.plots import Plotter

path = os.path.abspath(os.path.dirname(__file__))

# Optional constraints an example is designed to show.
EXAMPLE_OPTIONS = {
    "Operation_1Region_CHP-Variable-range": ["chp_operating_range"],
}


def available_examples():
    """Names of the example models shipped with Hypatia."""
    return sorted(
        name for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name, "sets"))
    )


def _check_name(example):
    examples = available_examples()
    if example not in examples:
        raise ValueError(f"Unknown example '{example}'. Available examples: {examples}")


def load_example(example, optimization="Single"):
    """Build one of the example models, with its input data already read.

    Parameters
    -----------
    example : str
        One of available_examples(), e.g. "Planning_1Region" or "Atlantis".
    optimization : str
        "Single", "MinEm" or "Multi", as in hypatia.Model.

    Returns
    -------
    hypatia.Model

    Example
    --------
    .. code-block:: python

        from hypatia import available_examples, load_example

        print(available_examples())
        model = load_example("Planning_1Region")
        print(model)
        model.run(solver="highs")
    """
    _check_name(example)
    folder = os.path.join(path, example)
    mode = "Operation" if example.startswith("Operation") else "Planning"

    model = Model(
        path=os.path.join(folder, "sets"),
        mode=mode,
        optimization=optimization,
        ensure_feasibility="Yes" if "UnMetDemand" in example else "No",
        name=example,
        optional_constraints=EXAMPLE_OPTIONS.get(example),
    )
    model.read_input_data(os.path.join(folder, "parameters"))

    config_path = os.path.join(folder, "config.xlsx")
    if os.path.exists(config_path):
        model.load_plots = lambda: Plotter(model, config_path, mode == "Operation")

    return model


def download_example(example, destination_path):
    """Copy the files of an example model to destination_path, to edit them.

    Parameters
    -----------
    example : str
        One of available_examples().
    destination_path : str
        Folder to create; it must not exist yet.
    """
    _check_name(example)
    shutil.copytree(src=os.path.join(path, example), dst=destination_path)
