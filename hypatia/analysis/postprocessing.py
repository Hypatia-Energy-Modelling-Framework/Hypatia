# -*- coding: utf-8 -*-
"""
Postprocessing of results. Reshaping the raw CVXPY value to pd.DataFrame
in nested dict of results.
"""

RESULT_MAP = {
    "production_by_tech": {
        "index": "year_slice",
        "var": 'results.variables["productionbyTechnology"]',
    },
    "use_by_tech": {
        "index": "year_slice",
        "var": 'results.variables["usebyTechnology"]',
    },
    "variable_cost": {"index": "years", "var": "results.cost_variable",},
    "decommissioning_cost": {"index": "years", "var": "results.cost_decom",},
    "new_capacity": {"index": "years", "var": 'results.variables["newcapacity"]',},
    "decommissioned_capacity": {
        "index": "years",
        "var": "results.decommissioned_capacity",
    },
    "decomisioning_cost": {"index": "years", "var": "results.cost_decom",},
    "total_capacity": {"index": "years", "var": "results.totalcapacity",},
    "fix_cost": {"index": "years", "var": "results.cost_fix",},
    "imports": {"index": "year_slice", "var": 'results.variables["line_import"]',},
    "exports": {"index": "year_slice", "var": 'results.variables["line_export"]',},
    "investment_cost": {"index": "years", "var": "results.cost_inv",},
    "fix_tax_cost": {"index": "years", "var": "results.cost_fix_tax"},
    "fix_tax_subsidies": {"index": "years", "var": "results.cost_fix_sub"},
    "emission_cost": {"index": "years", "var": "results.emission_cost"},
    "CO2_equivalent": {"index": "years", "var": "results.CO2_equivalent"},
}

# --TODO-- Add the line vars


import pandas as pd
import numpy as np
import os


def dict_to_csv(Dict, path):
    """Writes nested dicts  to csv"""

    for key, value in Dict.items():
        if isinstance(value, pd.DataFrame):
            value.to_csv(f"{path}//{key}.csv")
        else:
            new_path = f"{path}//{key}"
            os.mkdir(new_path)
            dict_to_csv(value, new_path)


def year_slice_index(
    years, time_fraction,
):

    try:
        return pd.MultiIndex.from_product(
            [years, list(range(1, len(time_fraction) + 1))],
        )
    except TypeError:
        return pd.MultiIndex.from_product([years, [1]])


def set_DataFrame(
    results, regions, years, time_fraction, glob_mapping, technologies, mode
):
    """Creates pd.DataFrame from reulsts"""

    _years = glob_mapping["Years"]
    years = _years[_years["Year"].isin(years)]["Year_name"]

    year_slice = year_slice_index(years, time_fraction)

    vars_frames = {}

    for item, info in RESULT_MAP.items():
        try:
            var = eval(info["var"])
        except (KeyError, AttributeError):
            continue
        vars_frames[item] = {}

        for region in regions:
            vars_frames[item][region] = {}

            for _type, values in var[region].items():
                if (item == "use_by_tech") and (_type == "supply"):
                    continue
                if item in ["imports", "exports"]:
                    columns = glob_mapping
                if item in ["imports", "exports"]:
                    columns = glob_mapping["Carriers_glob"]["Carrier"]
                else:
                    columns = technologies[region][_type]
                if isinstance(values, np.ndarray):
                    values = values
                elif isinstance(values, (pd.DataFrame, pd.Series)):
                    values = values.values
                else:
                    values = values.value
                frame = pd.DataFrame(
                    data=values, index=eval(info["index"]), columns=columns,
                )

                vars_frames[item][region][_type] = frame
    vars_frames["demand"] = {
        rr: pd.DataFrame(
            data=results.demand[rr].values,
            index=year_slice,
            columns=results.demand[rr].columns,
        )
        for rr in regions
    }

    return vars_frames
