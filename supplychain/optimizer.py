"""PuLP implementation of the single-product, single-period 3-echelon LP."""
from pathlib import Path
import pandas as pd
import pulp

def solve_benchmark(data_dir="data/sample"):
    base = Path(data_dir)
    suppliers = pd.read_csv(base / "suppliers.csv")
    warehouses = pd.read_csv(base / "warehouses.csv")
    customers = pd.read_csv(base / "customers.csv")
    inbound = pd.read_csv(base / "inbound_routes.csv")
    outbound = pd.read_csv(base / "outbound_routes.csv")

    S = suppliers.supplier_id.tolist()
    W = warehouses.warehouse_id.tolist()
    C = customers.customer_id.tolist()

    model = pulp.LpProblem("SupplyChain_Optimizer_Benchmark", pulp.LpMinimize)
    x = {(r.supplier_id, r.warehouse_id):
         pulp.LpVariable(f"x_{r.supplier_id}_{r.warehouse_id}", lowBound=0)
         for r in inbound.itertuples()}
    y = {(r.warehouse_id, r.customer_id):
         pulp.LpVariable(f"y_{r.warehouse_id}_{r.customer_id}", lowBound=0)
         for r in outbound.itertuples()}

    inbound_rows = {(r.supplier_id, r.warehouse_id): r for r in inbound.itertuples()}
    outbound_rows = {(r.warehouse_id, r.customer_id): r for r in outbound.itertuples()}
    supplier_data = suppliers.set_index("supplier_id")
    warehouse_data = warehouses.set_index("warehouse_id")
    customer_data = customers.set_index("customer_id")

    model += (
        pulp.lpSum((supplier_data.loc[i, "purchase_price_inr_per_unit"]
                    + inbound_rows[i,k].transport_cost_inr_per_unit) * var
                   for (i,k), var in x.items())
        + pulp.lpSum((outbound_rows[k,j].transport_cost_inr_per_unit
                      + warehouse_data.loc[k, "handling_cost_inr_per_unit"]) * var
                     for (k,j), var in y.items())
    ), "Total_operating_cost_INR"

    for i in S:
        model += pulp.lpSum(var for (si,k), var in x.items() if si == i) <= supplier_data.loc[i, "capacity_units"], f"supply_{i}"
    for k in W:
        inbound_flow = pulp.lpSum(var for (i,w), var in x.items() if w == k)
        outbound_flow = pulp.lpSum(var for (w,j), var in y.items() if w == k)
        model += inbound_flow == outbound_flow, f"flow_balance_{k}"
        model += inbound_flow <= warehouse_data.loc[k, "capacity_units"], f"warehouse_capacity_{k}"
    for j in C:
        model += pulp.lpSum(var for (k,c), var in y.items() if c == j) == customer_data.loc[j, "demand_units"], f"demand_{j}"
    for (i,k), var in x.items():
        model += var <= inbound_rows[i,k].capacity_units, f"inbound_capacity_{i}_{k}"
    for (k,j), var in y.items():
        model += var <= outbound_rows[k,j].capacity_units, f"outbound_capacity_{k}_{j}"

    # Every outbound route in this benchmark meets its customer's time window.
    for (k,j), route in outbound_rows.items():
        if route.lead_time_hours > customer_data.loc[j, "max_delivery_hours"]:
            model += y[k,j] == 0, f"delivery_window_{k}_{j}"

    status_code = model.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[status_code]
    if status != "Optimal":
        return {"status": status, "objective_cost_inr": None,
                "inbound": {}, "outbound": {}}

    inbound_alloc = {f"{i}->{k}": round(var.value() or 0, 8) for (i,k), var in x.items()}
    outbound_alloc = {f"{k}->{j}": round(var.value() or 0, 8) for (k,j), var in y.items()}
    return {
        "status": status,
        "objective_cost_inr": float(pulp.value(model.objective)),
        "inbound": inbound_alloc,
        "outbound": outbound_alloc,
        "model": model
    }
