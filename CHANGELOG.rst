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
