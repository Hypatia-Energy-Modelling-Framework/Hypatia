# -*- coding: utf-8 -*-

"""
This module contains the utility functions from cerating the optimization problem
"""

import cvxpy as cp
import numpy as np
import pandas as pd
import math as mt


def stack(a, b, axis=0):

    """
    concat cvxpy variable rows or columns
    """

    if axis == 0:
        return cp.vstack([a, b])
    elif axis == 1:
        return cp.hstack([a, b])
                
def newcap_accumulated(newcap, techs, main_years, tlft,period_step):

    """
    Calculates the accumulated new capacity of each technology in each 
    year of the model horizon based on the useful technical lifetime
    """

    index = pd.MultiIndex.from_product([techs, main_years])
    exist = pd.DataFrame(0, index=index, columns=index)

    newcap_reshape = cp.reshape(newcap, (len(main_years) * len(techs), 1))

    for tech in techs:
        for year in main_years:
            for year0 in main_years:

                age = (main_years.index(year) - main_years.index(year0))*period_step

                if age >= 0 and age < tlft[tech].values:

                    exist.loc[(tech, year), (tech, year0)] = 1

    accumulated_newcap_reshape = exist.values @ newcap_reshape
    accumulated_newcap = cp.reshape(accumulated_newcap_reshape, newcap.shape)

    return accumulated_newcap


def _calc_variable_overall(
    glob_technologies, regions, main_years, technologies, variable
):

    """
    Calculates the aggregated annual total or new capacity of each technology 
    over all the regions
    """

    variable_overall = {}
    for tech in list(
        glob_technologies.loc[glob_technologies["Tech_category"] != "Demand"][
            "Technology"
        ]
    ):
        variable_overall[tech] = np.zeros((len(main_years), 1))
        for reg in regions:
            for key, value in technologies[reg].items():

                if tech in value:

                    variable_overall[tech] += variable[reg][key][:, value.index(tech)]

    return variable_overall


def _calc_production_overall(
    glob_technologies, regions, main_years, technologies, variable
):

    """
    Calculates the aggregated annual production of each technology 
    over all the regions
    """

    production_overall = {}
    for tech in list(
        glob_technologies.loc[
            (glob_technologies["Tech_category"] != "Demand")
            & (glob_technologies["Tech_category"] != "Storage")
        ]["Technology"]
    ):
        production_overall[tech] = np.zeros((len(main_years), 1))
        for reg in regions:
            for key, value in technologies[reg].items():

                if tech in value:

                    production_overall[tech] += variable[reg][key][:, value.index(tech)]

    return production_overall


def line_newcap_accumulated(line_newcap, carriers, main_years, line_tlft, period_step):

    """
    Calculates the accumulated new capacity of each inter-regional link in each 
    year the model horizon based on the useful technical lifetime
    """
    #line_newcap = cp.multiply(line_lumpy_inv,line_cap) # we need to check if this woon't give us a size error (one-row vector multiplied to the matrix)
    index_line = pd.MultiIndex.from_product([carriers, main_years])
    exist_line = pd.DataFrame(0, index=index_line, columns=index_line)

    line_newcap_reshape = cp.reshape(line_newcap, (len(main_years) * len(carriers), 1))

    for carrier in carriers:
        for year in main_years:
            for year0 in main_years:

                age = (main_years.index(year) - main_years.index(year0))*period_step

                if age >= 0 and age < line_tlft[carrier].values:

                    exist_line.loc[(carrier, year), (carrier, year0)] = 1

    line_newacp_accumulated_reshape = exist_line.values @ line_newcap_reshape

    line_newcap_accumulated = cp.reshape(
        line_newacp_accumulated_reshape, line_newcap.shape
    )

    return line_newcap_accumulated


def line_newcap_lump_accumulated(line_newcap_lump, carriers, main_years, line_tlft, period_step):

    """
    Calculates the accumulated new capacity of each inter-regional link in each 
    year the model horizon based on the useful technical lifetime
    """
    #line_newcap = cp.multiply(line_lumpy_inv,line_cap) # we need to check if this woon't give us a size error (one-row vector multiplied to the matrix)
    index_line = pd.MultiIndex.from_product([carriers, main_years])
    exist_line = pd.DataFrame(0, index=index_line, columns=index_line)

    line_newcap_lump_reshape = cp.reshape(line_newcap_lump, (len(main_years) * len(carriers), 1))

    for carrier in carriers:
        for year in main_years:
            for year0 in main_years:

                age = (main_years.index(year) - main_years.index(year0))*period_step

                if age >= 0 and age < line_tlft[carrier].values:

                    exist_line.loc[(carrier, year), (carrier, year0)] = 1

    line_newacp_lump_accumulated_reshape = exist_line.values @ line_newcap_lump_reshape

    line_newcap_lump_accumulated = cp.reshape(
        line_newacp_lump_accumulated_reshape, line_newcap_lump.shape
    )

    return line_newcap_lump_accumulated



def decomcap(newcap, techs, main_years, tlft, period_step):

    """
    Calculates the annual decomissioned capacity of each technology in each
    year of the time horizon based on life time of the new capacities 
    installed in the vintage years
    """
    index = pd.MultiIndex.from_product([techs, main_years])
    decom_matrix = pd.DataFrame(0, index=index, columns=index)
    newcap_reshape = cp.reshape(newcap, (len(main_years) * len(techs), 1))

    for tech in techs:
        for indx, year in enumerate(main_years):

            try:

                decom_matrix.loc[
                    (tech, main_years[mt.ceil(indx + (tlft[tech].values)/period_step)]), (tech, year)
                ] = 1

            except:
                pass

    decomcap_reshape = decom_matrix.values @ newcap_reshape
    decomcap = cp.reshape(decomcap_reshape, newcap.shape)
    return decomcap


def line_decomcap(line_newcap, carriers, main_years, line_tlft, period_step):

    """
    Calculates the annual decomissioned capacity of each inter-regional link in each
    year of the time horizon based on life time of the new capacities 
    installed in the vintage years
    """
    index_line = pd.MultiIndex.from_product([carriers, main_years])
    decom_matrix_line = pd.DataFrame(0, index=index_line, columns=index_line)
    line_newcap_reshape = cp.reshape(line_newcap, (len(main_years) * len(carriers), 1))

    for carrier in carriers:
        for year in main_years:

            try:
                decom_matrix_line.loc[
                    (carrier, main_years[mt.ceil(main_years.index(year) + (line_tlft[carrier])/period_step)]),
                    (carrier, year),
                ] = 1

            except:
                pass
    line_decomcap_reshape = decom_matrix_line.values @ line_newcap_reshape
    line_decomcap = cp.reshape(line_decomcap_reshape, line_newcap.shape)
    return line_decomcap


# annual undiscounted investmnests and their related taxes and subsidies


def invcosts(inv, newcap, inv_tax, inv_sub):

    """
    Calculates the annual undiscounted investment cost of each technology and
    their taxes and subsidies before considering the annuities
    """

    cost_inv = cp.multiply(inv.values, newcap)
    specific_inv_tax = cp.multiply(inv_tax.values, inv.values)
    specific_inv_sub = cp.multiply(inv_sub.values, inv.values)
    cost_inv_tax = cp.multiply(specific_inv_tax, newcap)
    cost_inv_sub = cp.multiply(specific_inv_sub, newcap)

    return cost_inv, cost_inv_tax, cost_inv_sub


def invcosts_annuity(
    cost_inv_present,
    interest_rate,
    economiclife,
    technologies,
    main_years,
    discount_rate,
    period_step,
):

    """
    Calculates the annuities of the investment costs based on the interest rate
    and economic lifetime of each technology
    """

    depreciation = np.divide(
        np.multiply(
            np.power((interest_rate.values + 1), economiclife.values),
            interest_rate.values,
        ),
        (np.power((interest_rate.values + 1), economiclife.values) - 1),
    )
    depreciation = pd.DataFrame(
        depreciation, index=["Depreciation_rate"], columns=technologies
    )
    # EOH = main_years.index(main_years[-1])*period_step
    inv_fvalue_total = 0
    for tech_indx, tech in enumerate(technologies):
        inv_fvalue_discounted = 0
        for y_indx, year in enumerate(main_years):

            inv_fvalue_annual_discounted = 0
            for future_year in range(
                y_indx * period_step + 1, y_indx * period_step + economiclife.loc["Economic Life time", tech] + 1
            ):
            # for future_year in range(
            #     y_indx * period_step , EOH+1
            # ):
                annuity = (
                    cost_inv_present[y_indx, tech_indx]
                    * depreciation.loc["Depreciation_rate", tech]
                )

                inv_fvalue_annual_discounted += annuity * (
                    1 + discount_rate.loc[year, "Annual Discount Rate"]
                ) ** (-future_year)

            inv_fvalue_discounted += inv_fvalue_annual_discounted

        inv_fvalue_total += inv_fvalue_discounted

    return inv_fvalue_total


# annual undiscounted fixed O&M costs and their related taxes and subsidies


def fixcosts(fix, totalcap, fix_tax, fix_sub):

    """
    Calculates the annual undiscounted fixed operation and maintenance costs
    and their taxes and subsidies
    """

    cost_fix = cp.multiply(fix.values, totalcap)
    specific_fix_tax = cp.multiply(fix_tax.values, fix.values)
    specific_fix_sub = cp.multiply(fix_sub.values, fix.values)
    cost_fix_tax = cp.multiply(specific_fix_tax, totalcap)
    cost_fix_sub = cp.multiply(specific_fix_sub, totalcap)

    return cost_fix, cost_fix_tax, cost_fix_sub


def varcost(specific_varcost, activity, time_step):

    """
    Calculates the annual undiscounted variables costs
    """

    specific_varcost_reshape = pd.concat(
        [specific_varcost] * len(time_step)
    ).sort_index()
    variablecost = cp.multiply(specific_varcost_reshape.values, activity)

    return variablecost


def available_resource_prod(
    totalcap, capacity_factor, timeslice_fraction, annualprod_per_unitcapacity
):

    """
    Calculates the maximum available production due to the resource availability
    """

    available_capacity = cp.multiply(totalcap, capacity_factor)
    annualprod = cp.multiply(available_capacity, annualprod_per_unitcapacity)
    annual_prod_per_timslice = cp.multiply(annualprod, timeslice_fraction)

    return annual_prod_per_timslice


def annual_activity(activity, main_years, timeslices):

    """
    Calculates the annual production from the prodution defined on timeslices
    """
    activity_annual = cp.sum(activity[0 : len(timeslices), :], axis=0, keepdims=True)

    for indx, year in enumerate(main_years[1:]):

        activity_annual_rest = cp.sum(
            activity[(indx + 1) * len(timeslices) : (indx + 2) * len(timeslices), :],
            axis=0,
            keepdims=True,
        )
        activity_annual = stack(activity_annual, activity_annual_rest)

    return activity_annual


def line_varcost(
    specific_varcost, line_import, main_years, time_slices, lines
):

    """
    Calculates the annual undiscounted variables costs of inter-regional links
    """

    variablecost_line = {}

    for reg in line_import.keys():

        variablecost_line_regional = {}

        for key, value in line_import[reg].items():

            line_import_anunual = annual_activity(value, main_years, time_slices)

            if "{}-{}".format(reg, key) in lines:

                specific_varcost_line = specific_varcost.loc[
                    :, "{}-{}".format(reg, key)
                ]

            elif "{}-{}".format(reg, key) in lines:

                specific_varcost_line = specific_varcost.loc[
                    :, "{}-{}".format(key, reg)
                ]

            variablecost_line_regional[key] = cp.multiply(
                specific_varcost_line, line_import_anunual
            )

        variablecost_line[reg] = variablecost_line_regional

    return variablecost_line


def salvage_factor(
    main_years, technologies, tlft, interest_rate, discount_rate, economiclife, period_step
):

    """
    Calculates the salvage factor of the investment cost for the capacities
    that remain after the end of the time horizon 
    """

    salvage_factor_0 = pd.DataFrame(0, index=main_years, columns=technologies)

    rates_factor = pd.DataFrame(0, index=main_years, columns=technologies)

    EOH = main_years.index(main_years[-1])*period_step

    for tech in technologies:

        technical_factor = (1 - 1 / (1 + interest_rate[tech].values)) / (
            1 - 1 / ((1 + interest_rate[tech].values) ** economiclife[tech].values)
        )

        social_factor = (
            1 - 1 / ((1 + discount_rate.values) ** economiclife[tech].values)
        ) / (1 - 1 / (1 + discount_rate.values))

        rates_factor.loc[:, tech] = technical_factor * social_factor

        for indx, year in enumerate(main_years):

            if indx*period_step + tlft[tech].values > EOH:

                salvage_factor_0.loc[year, tech] = (
                    (1 + discount_rate.loc[year, :].values)
                    ** (tlft[tech].values - EOH - 1 + indx*period_step) - 1
                    
                ) / ((1 + discount_rate.loc[year, :].values) ** tlft[tech].values -1 )

    salvage_factor_mod = pd.DataFrame(
        salvage_factor_0.values * rates_factor.values,
        index=main_years,
        columns=technologies,
    )

    return salvage_factor_mod


def salvage_factor_line(
    main_years, carriers , tlft, interest_rate, discount_rate, economiclife, period_step
):

    """
    Calculates the salvage factor of the investment cost for the capacities
    that remain after the end of the time horizon
    """

    salvage_factor_0_line = pd.DataFrame(0, index=main_years, columns=carriers)

    rates_factor_line = pd.DataFrame(0, index=main_years, columns=carriers)

    EOH = main_years.index(main_years[-1])*period_step

    for  carrier in carriers:

        technical_factor_line = (1 - 1 / (1 + interest_rate[carrier].values)) / (
            1 - 1 / ((1 + interest_rate[carrier].values) ** economiclife[carrier].values)
        )

        social_factor_line = (
            1 - 1 / ((1 + discount_rate.values) ** economiclife[carrier].values)
        ) / (1 - 1 / (1 + discount_rate.values))

        rates_factor_line.loc[:, carrier] = technical_factor_line * social_factor_line

        for indx, year in enumerate(main_years):

            if indx*period_step + tlft[carrier].values > EOH:

                salvage_factor_0_line.loc[year, carrier] = (
                    (1 + discount_rate.loc[year, :].values)
                    ** (tlft[carrier].values - EOH - 1 + indx*period_step)
                    -1
                ) / ((1 + discount_rate.loc[year, :].values) ** tlft[carrier].values - 1)

    salvage_factor_mod_line = pd.DataFrame(
    salvage_factor_0_line.values * rates_factor_line.values,
    index=main_years,
    columns=carriers,
    )

    return salvage_factor_mod_line
# def storage_state_of_charge(initial_storage, flow_in, flow_out, main_years, time_steps,charge_efficiency,discharge_efficiency):

#     """
#     Calculates the state of charge of the storage 
#     """
#     charge_efficiency_reshape = pd.concat(
#     [charge_efficiency]
#     * len(time_steps)
#     ).sort_index()

#     discharge_efficiency_reshape = pd.concat(
#     [discharge_efficiency]
#     * len(time_steps)
#     ).sort_index()

#     initial_storage_concat = pd.concat(
#         [initial_storage] * len(time_steps) * len(main_years)
#     )

#     state_of_charge = cp.multiply(cp.cumsum(flow_in),charge_efficiency_reshape) + initial_storage_concat - \
#         cp.multiply(cp.cumsum(flow_out),(np.ones((discharge_efficiency_reshape.shape))/discharge_efficiency_reshape.values))

#     return state_of_charge

def storage_state_of_charge(initial_storage, flow_in, flow_out, main_years, time_steps,charge_efficiency,discharge_efficiency):

    """
    Calculates the state of charge of the storage 
    """

    charge_efficiency_reshape = pd.concat(
    [charge_efficiency]
    * len(time_steps)
    ).sort_index()

    discharge_efficiency_reshape = pd.concat(
    [discharge_efficiency]
    * len(time_steps)
    ).sort_index()

    initial_storage_concat = pd.concat(
        [initial_storage] * len(time_steps)
    ).sort_index()

    state_of_charge = cp.multiply(cp.cumsum(flow_in[0 : len(time_steps), :]),
                                  charge_efficiency_reshape.loc[main_years[0],:]) + initial_storage_concat.loc[main_years[0],:] -\
        cp.multiply(cp.cumsum(flow_out[0 : len(time_steps), :]), (np.ones((discharge_efficiency_reshape.loc[main_years[0],:].shape))/discharge_efficiency_reshape.loc[main_years[0],:].values))
        
    for indx, year in enumerate(main_years[1:]):

        state_of_charge_rest = cp.multiply(cp.cumsum(flow_in[(indx + 1) * len(time_steps) : (indx + 2) * len(time_steps), :]),
                                      charge_efficiency_reshape.loc[year,:]) + initial_storage_concat.loc[year,:] -\
            cp.multiply(cp.cumsum(flow_out[(indx + 1) * len(time_steps) : (indx + 2) * len(time_steps), :]), (np.ones((discharge_efficiency_reshape.loc[year,:].shape))/discharge_efficiency_reshape.loc[year,:].values))
        state_of_charge = stack(state_of_charge, state_of_charge_rest)
                                

    return state_of_charge


def get_regions_with_storage(sets):

    """
    Finds the regions with storage technologies
    """

    for reg in sets.regions:

        if "Storage" in sets.Technologies[reg]:

            yield reg


def storage_max_flow(
    storage_totalcapacity, time, storage_capacity_factor, timeslice_fraction
):
    """
    Calculates the maximum allowed inflow and ouflow of storage technologies 
    based on the charge/discharge time and the total nominal capacity
    """

    storage_capacity_available = cp.multiply(
        storage_totalcapacity, storage_capacity_factor
    )

    max_flow = cp.multiply(storage_capacity_available, timeslice_fraction) * 8760 / time

    return max_flow


def vicenty(coord1,coord2):
    
    """
    Vincenty's inverse method formula to calculate the distance in meters
    between two points on the surface of a spheroid (WGS84).
    inspired by Calliope, modified from https://github.com/maurycyp/vincenty
    """
    a = 6378137  # equitorial radius in meters
    f = 1 / 298.257223563  # flattening from sphere to oblate spheroid
    b = a * (1 - f)  # polar radius in meters

    max_iter = 200
    thresh = 1e-12

    # short-circuit coincident points
    if coord1[0] == coord2[0] and coord1[1] == coord2[1]:
        return 0
    U1 = np.arctan((1-f)*np.tan(np.radians(coord1[0])))
    U2 = np.arctan((1 - f) * np.tan(np.radians(coord2[0])))
    L = np.radians(coord2[1] - coord1[1])
    Lambda = L
    
    sinU1 = np.sin(U1)
    cosU1 = np.cos(U1)
    sinU2 = np.sin(U2)
    cosU2 = np.cos(U2)
    
    for iteration in range(max_iter):
        sinLambda = np.sin(Lambda)
        cosLambda = np.cos(Lambda)
        sinSigma = np.sqrt((cosU2 * sinLambda) ** 2 +
                             (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
        if sinSigma == 0:
            return 0.0  # coincident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = np.arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha ** 2
        
        try:
            cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        except ZeroDivisionError:
            cos2SigmaM = 0
            
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        LambdaPrev = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * (
            sigma + C * sinSigma * (
                cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM ** 2))
        )

        if abs(Lambda - LambdaPrev) < thresh:
            break  # successful convergence
    else:
        return None  # failure to converge
    uSq = cosSqAlpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma *
                 (-1 + 2 * cos2SigmaM ** 2) - B / 6 * cos2SigmaM *
                 (-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
    D = b * A * (sigma - deltaSigma)

    return round(D)/1000
    
    
    
    
