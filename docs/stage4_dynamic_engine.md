# Stage 4 — Dynamic Optimisation Engine

## What changed
- Replaced fixed benchmark dimensions with row-driven supplier, warehouse, customer and route sets.
- Generates flow-balance, supply, throughput, demand, route-capacity and delivery-window constraints automatically.
- Adds optional total-emissions epsilon constraint.
- Returns cost reconciliation, route allocations, supplier/warehouse utilisation, route capacity slack, delivery KPI and emissions.
- Returns solver status and a diagnostic when no optimal solution is found.

## Mathematical formulation
For inbound arcs (i,k), outbound arcs (k,j), continuous flows x_ik and y_kj:

Minimise Σ_i,k (p_i + a_ik)x_ik + Σ_k,j (b_kj + h_k)y_kj

Subject to supplier capacity, warehouse flow conservation, warehouse throughput, exact customer demand, route capacities, delivery-window route eligibility, and non-negativity. If supplied, add Σ_i,k e_ik x_ik + Σ_k,j f_kj y_kj ≤ E_max.

## Interpretation
The objective is an operating-cost minimum, not a full inventory or vehicle-routing model. Warehouse throughput is a period capacity. Delivery KPI is the demand-weighted mean outbound lead time; it is reported, not optimised directly. Emissions are reported unless a cap is supplied.

## Reproducibility
Run `python run_optimisation.py`; optional arguments are `--data`, `--emissions-cap`, and `--output`. Run `python -m pytest -q` for regression and dynamic-dimension checks.
