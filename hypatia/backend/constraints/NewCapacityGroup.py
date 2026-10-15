from hypatia.backend.constraints._capacity_groups import CapacityGroupLimit

"""
Annual upper limit on the aggregated new capacity of user-defined technology
groups, summed over all regions. Active only if the sheets
"Capacity_group_membership" and "Max_newcap_group" are filled.
"""


class NewCapacityGroup(CapacityGroupLimit):
    VARIABLE = "real_new_capacity"
    LIMIT_KEY = "group_max_newcap"
    LIMIT_COLUMN = "Max_newcap"
