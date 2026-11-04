# Stage 5 — Scenario and Sensitivity Analysis

## Purpose

Stage 5 adds what-if analysis to the dynamic linear-programming engine. A scenario modifies a copy of the input tables and then calls the same `solve_network` optimisation function. The baseline tables and baseline result are not overwritten.

## Run

```bash
python run_scenarios.py
```

Run the standard scenarios plus a supplier S1 purchase-price sensitivity grid:

```bash
python run_scenarios.py --price-sensitivity
```

Choose a different input bundle or output path:

```bash
python run_scenarios.py --data data/sample --output reports/my_scenario_run.json
```

## Included scenarios

1. **Supplier price shock:** raises the selected supplier's purchase price by a percentage.
2. **Supplier disruption:** sets the selected supplier's available capacity and its inbound route capacities to zero.
3. **Demand growth:** scales all customer demand by a percentage.
4. **Warehouse capacity reduction:** reduces the selected warehouse's capacity by a percentage.
5. **Carbon cap:** re-solves the LP with an emissions epsilon-constraint.

The standard run uses S1 +10%, S1 outage, demand +20%, W2 capacity -25%, and a 1,200 kg CO2e cap.

## Sensitivity

The S1 price grid re-solves the model at 0%, 5%, 10%, 15%, and 20% price increases. Each row includes the resulting objective cost, cost change, emissions, delivery time, and changed route allocations.

## Interpreting results

- A positive `cost_change_inr` means the scenario is more expensive than the baseline.
- A negative value means the scenario reduced the optimal objective cost.
- A non-optimal solver status means the scenario did not produce a usable optimal allocation. Check the scenario's diagnostic and validation warnings.
- A carbon cap may make the LP infeasible if no network allocation can satisfy demand under that limit.
- Allocation changes show only routes whose flow differs from baseline by more than numerical tolerance.

## Modelling limitations

The model remains a deterministic, single-period, single-product, continuous-flow LP. It does not model fixed supplier activation costs, integer shipment sizes, vehicle routing, inventory carried between periods, uncertain demand, or lead-time variability. A supplier outage is represented by zero available supply and zero inbound route capacity.

## Research interpretation

Scenario analysis evaluates discrete business shocks. Sensitivity analysis evaluates a parameter over a specified range. This is not the same as formal LP dual-price or allowable-range sensitivity analysis; those can be added as a later research extension.


## Scenario disruption validation correction

A deliberate zero-capacity supplier/route is now accepted as a valid scenario input. Scenario-mode validation skips only aggregate-capacity prechecks, allowing the LP solver to return `Infeasible` when the disruption makes demand impossible to satisfy. Normal uploaded source-data validation continues to enforce aggregate-capacity checks. Failed scenario solves no longer produce misleading route-allocation deltas.
