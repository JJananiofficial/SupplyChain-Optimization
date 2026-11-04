# Stage 6 — Cost–Emissions Pareto Analysis

## Purpose
Stage 6 adds multi-objective decision support to the deterministic single-period supply-chain LP. It uses the **epsilon-constraint method**: minimise operating cost while constraining total CO2e emissions to a specified cap.

## Procedure
1. Solve a separate LP minimising total emissions. This establishes the minimum feasible emissions endpoint under the current network and constraints.
2. Solve the ordinary cost-minimisation LP. This establishes the cost-optimal endpoint and its associated emissions.
3. Generate evenly spaced emissions caps between those endpoints.
4. Re-solve the cost-minimisation LP for every cap.
5. Retain feasible solutions and identify non-dominated cost/emissions pairs.
6. Export the full sweep and Pareto frontier to JSON and CSV.

## Run
```bash
python run_pareto.py
python run_pareto.py --points 21
python run_pareto.py --data data/sample --points 15 --output-dir reports/pareto
```

Outputs:
- `reports/pareto/pareto_analysis.json` — complete solutions and allocations
- `reports/pareto/pareto_sweep.csv` — every requested cap and its solver status
- `reports/pareto/pareto_frontier.csv` — non-dominated solutions

## Interpretation
- Lower emissions caps may be infeasible; the report records those statuses rather than inventing values.
- The minimum-emissions endpoint is calculated independently. It is not assumed to equal baseline emissions.
- A Pareto point is non-dominated if no other feasible solution has both lower-or-equal cost and lower-or-equal emissions with a strict improvement in at least one objective.
- Delivery time is reported as a third performance measure, but it is not an optimisation objective in this stage. A future three-objective extension could analyse cost, emissions and delivery jointly.

## Scope and limitations
The analysis inherits the project's current assumptions: one product, one period, continuous flows, deterministic demand and capacities, linear costs and emissions, and fixed routes. The frontier is sampled at a finite number of epsilon levels; it is not a proof that every possible efficient solution has been enumerated. Results depend on the supplied data and the accuracy of the emissions factors.
