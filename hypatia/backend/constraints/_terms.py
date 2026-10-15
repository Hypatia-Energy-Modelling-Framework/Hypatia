"""
Helpers shared by constraints that add up a variable number of cvxpy terms
or need to recognise the electricity carrier.

Kept in one place so that the definition of "power carrier" and the way terms
are summed cannot drift apart between constraints.
"""
from functools import reduce
import operator

import cvxpy as cp
import numpy as np

# Carrier names treated as electricity by power-sector constraints, compared
# after normalisation (case-insensitive, surrounding spaces ignored).
# Note: "Final_electricity" is deliberately NOT included.
POWER_CARRIERS = frozenset({"electricity", "power"})


def normalize_carrier(carrier) -> str:
    return str(carrier).strip().casefold()


def is_power_carrier(carrier) -> bool:
    return normalize_carrier(carrier) in POWER_CARRIERS


def sum_terms(terms, zero_shape=None):
    """Sum a list of cvxpy expressions.

    Returns None when there are no terms, or a zero constant of ``zero_shape``
    if one is given, so callers can skip a constraint instead of building an
    invalid one from an empty numpy accumulator.

    Uses ``a + b`` (via operator.add), never ``a += b``: recent cvxpy versions
    raise an error on in-place operations on expressions.
    """
    terms = list(terms)
    if not terms:
        return None if zero_shape is None else cp.Constant(np.zeros(zero_shape))
    return reduce(operator.add, terms)
