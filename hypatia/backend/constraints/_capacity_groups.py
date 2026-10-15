"""
Shared logic for upper limits on the capacity of user-defined technology groups.

For every group g listed in the limit sheet and every model year y:

    sum over t in g, over regions r of  CAP[r, t, y]  <=  LIMIT[g, y]

where CAP is either the total capacity or the new capacity, depending on the
subclass. Groups and limits are read from optional parameter sheets
(see CAPACITY_GROUP_SHEETS in utility.py): if the sheets are missing or empty
the constraint adds nothing, so models without groups are unchanged.
"""
from hypatia.backend.constraints.Constraint import Constraint
from hypatia.backend.constraints._terms import sum_terms
from hypatia.utility.constants import ModelMode
from hypatia.utility.utility import (
    capacity_group_limits_to_wide,
    capacity_group_membership_to_dict,
    get_optional_parameter_from_global_or_regional_file,
)


def capacity_by_group(settings, variable, membership):
    """Sum a capacity variable over the technologies of each group and over all regions.

    Returns {group name: cvxpy expression of shape (n_years,)}. The shape is
    the one of a single technology column, variable[reg][category][:, i], so
    it matches the limits taken from the sheet without any reshape.
    """
    n_years = len(settings.years)
    grouped = {}
    for group_name, techs in capacity_group_membership_to_dict(membership).items():
        terms = [
            variable[reg][category][:, members.index(tech)]
            for tech in techs
            for reg in settings.regions
            for category, members in settings.technologies[reg].items()
            if tech in members
        ]
        grouped[group_name] = sum_terms(terms, zero_shape=(n_years,))
    return grouped


class CapacityGroupLimit(Constraint):
    """Base class: subclasses only say which variable and which limit sheet to use."""

    MODES = [ModelMode.Planning]

    VARIABLE = None      # attribute of ModelVariables, e.g. "totalcapacity"
    LIMIT_KEY = None     # key of CAPACITY_GROUP_SHEETS, e.g. "group_maxtotcap"
    LIMIT_COLUMN = None  # value column of that sheet, e.g. "Max_totalcap"

    def _check(self):
        assert getattr(self.variables, self.VARIABLE, None) is not None, \
            f"{self.VARIABLE} must be defined"

    def _optional_table(self, key):
        return get_optional_parameter_from_global_or_regional_file(
            self.model_data.settings, self.model_data, key, key
        )

    def rules(self):
        membership = self._optional_table("capacity_group_membership")
        limits = self._optional_table(self.LIMIT_KEY)
        if membership is None or limits is None or limits.empty:
            return []

        settings = self.model_data.settings
        capacity = capacity_by_group(settings, getattr(self.variables, self.VARIABLE), membership)
        limits = capacity_group_limits_to_wide(limits, settings.years, self.LIMIT_COLUMN)

        return [
            capacity[group_name] <= limits[group_name].values.astype(float)
            for group_name in limits.columns
        ]
