Release History
===============

Unreleased
----------
* **Enhancement**: optional constraints (``chp_operating_range``, ``production_ramp``,
  ``min_tech_power_output``, ``electrolysis_consumption``, ``boolean_for_storage``)
  are now enabled per model with ``Model(..., optional_constraints=[...])`` instead
  of uncommenting lines in ``ConstraintList.py``. The default (none enabled) builds
  the same problem as before. The JRP Nucleare runs correspond to
  ``optional_constraints=["chp_operating_range"]`` (tag ``jrp-nucleare-v1``).
* **CHPOperatingRange**: the number of CHP groups is the number of rows in the
  ``CHP_variable_techs_selection`` sheet (it was fixed to 5 in the code). Multi-region models now
  work: the global template used a key the constraint did not read. Missing or invalid
  efficiencies raise an error instead of silently producing NaN coefficients. Debug prints removed.
* **Parameter templates** can declare ``"variable_index": True``: the rows are user-defined and
  only the columns are validated.
* **Bug**: models without storage technologies failed with ``KeyError: 'storage_cyclic_boundary'``
  (the storage cycle parameter was read even when no region has storage). All examples were affected.
* **Bug**: multi-region models with transmission lines could not be solved by LP solvers: line
  efficiency ``eff ** (length / 100)`` was written with ``cp.exp`` on input data, which cvxpy turned
  into an exponential cone. Now computed with numpy (same values).
* **Examples**: all examples load again. Missing parameter sheets added with their default values
  (which leave the related constraints inactive); Atlantis and Neverland restored from the old main.
  ``available_examples()``, ``load_example(name)`` and ``download_example(name, path)`` are exported
  from ``hypatia`` and work with every example folder.
* **Feature**: upper limits on the total and new capacity of user-defined groups of
  technologies, summed over regions (``TotalCapacityGroup``, ``NewCapacityGroup``).
  Groups go in the sheet ``Capacity_group_membership`` (Group, Technology) and limits in
  ``Max_totalcap_group`` / ``Max_newcap_group`` (Group, Year, value), in the regional
  parameter file for single-region models and in the global file for multi-region ones.
  Years use the model year codes (e.g. ``Y0``). Without these sheets nothing changes.
* **Bug**: EmissionCapRegional/Global, LandUsageGlobal and RenewableProductionRegional/Global
  built an invalid constraint (numpy array instead of cvxpy) when no matching term existed,
  and recognised the electricity carrier only if named exactly ``Electricity``. Fixes from
  May 2026 (old main, ``6b53b2c`` and ``fee908b``) brought over; carrier names are now
  matched ignoring case and surrounding spaces (``Electricity``, ``Power``).
  ``Final_electricity`` is still not treated as electricity.
* **Refactoring**: shared helpers in ``constraints/_terms.py`` replace five local copies;
  terms are summed with ``a + b`` instead of ``a += b``, which recent cvxpy rejects.
* **Bug**: ``print(model)`` failed because ``Model`` had no ``settings`` attribute;
  ``Model.settings`` is now a read-only property.

0.1.1 (04/02/2022)
------------------
* **Bug**: Total capacity plot duplicating regions solved (issue #1).
* **Bug**: Results overwrite bug fixed (issue #3).
* **Enhacement**: Parameter sheets order modfied (issue #4)
* **Enhacement(backward-incompatible)**: Activity and capacity units and CO2 emission table added to the global set files (issue #5)
* **Enhacement**: autocompiled config file with the names and units (issue #6).
* **Enhacement**: Parameter sheet names' error handling improved (issue #7)
* **Docs**: Doc modification (example gallery, building a model,...).
