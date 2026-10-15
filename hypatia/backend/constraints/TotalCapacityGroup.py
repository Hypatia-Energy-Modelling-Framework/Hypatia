from hypatia.backend.constraints._capacity_groups import CapacityGroupLimit

"""
Annual upper limit on the aggregated total capacity of user-defined technology
groups, summed over all regions. Active only if the sheets
"Capacity_group_membership" and "Max_totalcap_group" are filled.
"""


class TotalCapacityGroup(CapacityGroupLimit):
    VARIABLE = "totalcapacity"
    LIMIT_KEY = "group_maxtotcap"
    LIMIT_COLUMN = "Max_totalcap"
