***********
Why CVXPY
***********

What is CVXPY
==============
`CVXPY <https://www.cvxpy.org>`_ is Python-based modelling language for convex optimization problems.
While, usually writing an optimization prblem needs to be in restrictive standard form required by
solvers, CVXPY lets the modeller to express an optimization problem in a natural way that follows the math. More than that,
CVXPY supports mixed-integer convest programs. More importantluy, CVXPY allows the modeller to **vectorize** the model that fasten the preprocessing of the problem
for the solver. `Vectorized problems vs. scalar problems <https://github.com/cvxpy/cvxpy/blob/master/examples/notebooks/building_models_with_fast_compile_times.ipynb>`_,
avoids multiple nested **for loops** in the preprocessing which for large problems become extremely time consuming.

In this document, we tested the performance of CVXPY vs. `Pyomo <https://github.com/Pyomo/pyomo>`_ as the most popular Python optimization library for energy modellers.
In order to test the performance in terms of time to build a unique optimization problem, we create a dummy multi node energy model with hourly time resolution and capacity expansion in
Pyomo and CVXPY. We set the iteration limit of the solver equal to 1 to avoid the solver, solving the problem. As a result, we will test only the performance of the two libraries
in terms of generating and loading the problem to the solver. Moreover, through this example, we show how defining a problem in CVXPY is close to mathematical language of the problem.

The data that are used for the test are available in github along with the jupyter notebook.

Pyomo Version
---------------

.. code-block:: python

    model = AbstractModel()

    # Definition of sets
    model.years = Set(initialize=lambda model: years)
    model.hours = Set(initialize=lambda model: hours)
    model.techs = Set(initialize=lambda model: techs)
    model.regs = Set(initialize=lambda model: regions)

    # Definition of Vars
    model.production = Var(
        model.years, model.hours, model.techs, model.regs, domain=NonNegativeReals
    )
    model.new_capacity = Var(
        model.years, model.techs, model.regs, domain=NonNegativeReals
    )
    model.total_capacity = Var(
        model.years, model.techs, model.regs, domain=NonNegativeReals
    )
    # Definition of paramters
    model.inv_cost = Param(
        model.years,
        model.techs,
        model.regs,
        initialize=lambda model, y, t, r: inv_cost.loc[y, t],
    )
    model.var_cost = Param(
        model.years,
        model.techs,
        model.regs,
        initialize=lambda model, y, t, r: var_cost.loc[y, t],
    )

    model.availability = Param(
        model.years,
        model.hours,
        model.techs,
        model.regs,
        initialize=lambda model, y, h, t, r: availability.loc[(y, h), t],
    )
    model.demand = Param(
        model.years,
        model.hours,
        model.regs,
        initialize=lambda model, y, h, r: demand.loc[(y, h), "demand"],
    )

    # Definition of rules
    def tot_cap(model, y, t, r):
        if y == years[0]:
            return model.total_capacity[y, t, r] == model.new_capacity[y, t, r]
        return (
            model.total_capacity[y, t, r]
            == model.total_capacity[y - 1, t, r] + model.new_capacity[y, t, r]
        )

    def demand_prod(model, y, h, r):
        return (
            sum(model.production[y, h, t, r] for t in model.techs)
            == model.demand[y, h, r]
        )

    def availability_prod(model, y, h, t, r):
        return (
            model.production[y, h, t, r]
            <= model.total_capacity[y, t, r] * model.availability[y, h, t, r]
        )

    def objective_function(model):

        tot_inv = sum(
            model.inv_cost[y, t, r] * model.new_capacity[y, t, r]
            for y in model.years
            for t in model.techs
            for r in model.regs
        )
        tot_var = sum(
            model.var_cost[y, t, r]
            * sum(model.production[y, h, t, r] for h in model.hours)
            for y in model.years
            for t in model.techs
            for r in model.regs
        )
        return tot_inv + tot_var

    model.balance_rule = Constraint(
        model.years, model.hours, model.regs, rule=demand_prod
    )
    model.availability_rule = Constraint(
        model.years, model.hours, model.techs, model.regs, rule=availability_prod
    )
    model.capacity_rule = Constraint(model.years, model.techs, model.regs, rule=tot_cap)
    model.OBJ = Objective(rule=objective_function, sense=minimize)

    instance = model.create_instance()

    opt = SolverFactory(solver)


CVXPY Version
-------------
.. code-block:: python

    constraints = []
    tot_var_cost = 0
    tot_inv_cost = 0

    for rr in regions:
        # Creting variables
        production = cp.Variable(
            shape=(len(years) * len(hours), len(techs)),
            nonneg=True,
        )

        new_capacity = cp.Variable(shape=(len(years), len(techs)), nonneg=True)

        # meeting the demand
        constraints.append(
            cp.sum(production, axis=1) == demand.loc[years, "demand"].values
        )

        # total capacity -> cummulative sum of new capacity assuming
        # there is no disposed capacity
        if len(years) == 1:
            total_capacity = new_capacity
        else:
            total_capacity = cp.cumsum(new_capacity)

        # Production lower than the available capacity

        for yy, year in enumerate(years):
            constraints.append(
                production[yy * 8760 : (yy + 1) * 8760, :]
                <= cp.multiply(
                    total_capacity[yy : yy + 1, :],
                    availability.loc[(year, slice(None)), :].values,
                )
            )

            tot_var_cost += cp.sum(
                cp.multiply(
                    cp.sum(production[yy * 8760 : (yy + 1) * 8760, :], axis=0),
                    var_cost.loc[year, :].values,
                )
            )
        tot_inv_cost += cp.sum(cp.multiply(new_capacity, inv_cost.loc[years, :].values))

    # Definition of objective function
    objective = cp.Minimize(tot_var_cost + tot_inv_cost)

    # Problem definition
    problem = cp.Problem(objective=objective, constraints=constraints)
    probblem.solve()


Results
---------
Testing the two models for 2 nodes and changing the number of years, CVXPY always show a better performance in terms of time needed
to generate the model. While for small problems, the difference is quiete negligible, for big problems, the difference is so considerable as shown
in the figure. Moreover, writing an optimization problem in CVXPY is usually more transparent that can help energy modellers without professional coding
skills understand the models and contribute to the development easier.

.. image:: _static/test_speed.png
   :align: center