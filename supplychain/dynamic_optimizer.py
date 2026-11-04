"""Dynamic LP engine for single-product, single-period supply-chain networks."""
from __future__ import annotations
from pathlib import Path
from typing import Mapping
import pandas as pd
import pulp
from .data_validation import validate_tables, REQUIRED_COLUMNS


def solve_network(tables: Mapping[str, pd.DataFrame], emissions_cap_kg: float | None = None,
                  solver_msg: bool = False, scenario_mode: bool = False, objective_mode: str = "cost") -> dict:
    """Solve a data-driven min-cost flow LP for any valid network dimensions.

    emissions_cap_kg optionally activates an epsilon-constraint on total CO2e.
    Continuous shipment quantities are used; no integer/vehicle decisions.
    """
    if objective_mode not in {"cost", "emissions"}:
        return {"status": "Invalid data", "errors": ["objective_mode must be cost or emissions"], "warnings": []}
    # Scenario mode lets the LP solver classify insufficient capacity as
    # Infeasible instead of rejecting a deliberate disruption as bad source data.
    report = validate_tables(tables, check_aggregate_capacity=not scenario_mode)
    if not report.is_valid:
        return {"status": "Invalid data", "errors": report.errors, "warnings": report.warnings}
    if emissions_cap_kg is not None and emissions_cap_kg < 0:
        return {"status": "Invalid data", "errors": ["emissions_cap_kg must be nonnegative"], "warnings": []}

    s, w, c = (tables[n].copy() for n in ("suppliers", "warehouses", "customers"))
    ir, oroutes = tables["inbound_routes"].copy(), tables["outbound_routes"].copy()
    # Normalise identifiers consistently; validation has already checked uniqueness/references.
    for df, cols in ((s,["supplier_id"]),(w,["warehouse_id"]),(c,["customer_id"]),
                     (ir,["supplier_id","warehouse_id"]),(oroutes,["warehouse_id","customer_id"])):
        for col in cols: df[col] = df[col].astype(str)
    sidx=s.set_index('supplier_id'); widx=w.set_index('warehouse_id'); cidx=c.set_index('customer_id')
    inbound={(r.supplier_id,r.warehouse_id):r for r in ir.itertuples(index=False)}
    outbound={(r.warehouse_id,r.customer_id):r for r in oroutes.itertuples(index=False)}
    x={a:pulp.LpVariable(f"in_{n}",lowBound=0) for n,a in enumerate(inbound)}
    y={a:pulp.LpVariable(f"out_{n}",lowBound=0) for n,a in enumerate(outbound)}
    model=pulp.LpProblem('SupplyChain_Dynamic_Optimisation',pulp.LpMinimize)
    procurement=pulp.lpSum(float(sidx.loc[i,'purchase_price_inr_per_unit'])*v for (i,k),v in x.items())
    inbound_cost=pulp.lpSum(float(inbound[a].transport_cost_inr_per_unit)*v for a,v in x.items())
    outbound_cost=pulp.lpSum(float(outbound[a].transport_cost_inr_per_unit)*v for a,v in y.items())
    handling_cost=pulp.lpSum(float(widx.loc[k,'handling_cost_inr_per_unit'])*v for (k,j),v in y.items())
    total_emissions=(pulp.lpSum(float(inbound[a].emissions_kg_co2e_per_unit)*v for a,v in x.items())+
                     pulp.lpSum(float(outbound[a].emissions_kg_co2e_per_unit)*v for a,v in y.items()))
    total_cost = procurement+inbound_cost+outbound_cost+handling_cost
    model += (total_cost if objective_mode == 'cost' else total_emissions), ('total_cost_inr' if objective_mode == 'cost' else 'total_emissions_kg_co2e')

    for i,row in sidx.iterrows():
        model += pulp.lpSum(v for (si,k),v in x.items() if si==i) <= float(row.capacity_units), f'supply_{i}'
    for k,row in widx.iterrows():
        inflow=pulp.lpSum(v for (i,wid),v in x.items() if wid==k)
        outflow=pulp.lpSum(v for (wid,j),v in y.items() if wid==k)
        model += inflow == outflow, f'flow_balance_{k}'
        model += inflow <= float(row.capacity_units), f'warehouse_capacity_{k}'
    for j,row in cidx.iterrows():
        model += pulp.lpSum(v for (k,cid),v in y.items() if cid==j) == float(row.demand_units), f'demand_{j}'
    for (i,k),v in x.items(): model += v <= float(inbound[i,k].capacity_units), f'inbound_capacity_{i}_{k}'
    for (k,j),v in y.items():
        if float(outbound[k,j].lead_time_hours) > float(cidx.loc[j,'max_delivery_hours']):
            model += v == 0, f'delivery_window_{k}_{j}'
        else:
            model += v <= float(outbound[k,j].capacity_units), f'outbound_capacity_{k}_{j}'
    if emissions_cap_kg is not None:
        model += total_emissions <= float(emissions_cap_kg), 'emissions_cap'

    solver=pulp.PULP_CBC_CMD(msg=solver_msg)
    code=model.solve(solver); status=pulp.LpStatus[code]
    if status != 'Optimal':
        return {"status":status,"objective_cost_inr":None,"solver_status_code":int(code),
                "diagnostic":"The LP has no optimal solution. Check demand, route eligibility, capacities, and any emissions cap.",
                "validation_warnings":report.warnings}

    val=lambda v: float(v.value() or 0.0)
    inbound_alloc=[{"supplier_id":i,"warehouse_id":k,"units":val(v)} for (i,k),v in x.items() if val(v)>1e-7]
    outbound_alloc=[{"warehouse_id":k,"customer_id":j,"units":val(v)} for (k,j),v in y.items() if val(v)>1e-7]
    inbound_em=float(pulp.value(pulp.lpSum(float(inbound[a].emissions_kg_co2e_per_unit)*v for a,v in x.items())))
    outbound_em=float(pulp.value(pulp.lpSum(float(outbound[a].emissions_kg_co2e_per_unit)*v for a,v in y.items())))
    total_demand=float(c.demand_units.sum())
    avg_delivery=sum(float(outbound[k,j].lead_time_hours)*val(v) for (k,j),v in y.items())/total_demand
    cost_parts={"procurement_inr":float(pulp.value(procurement)),"inbound_transport_inr":float(pulp.value(inbound_cost)),
                "outbound_transport_inr":float(pulp.value(outbound_cost)),"handling_inr":float(pulp.value(handling_cost))}
    supplier_util=[]
    for i,row in sidx.iterrows():
        used=sum(val(v) for (si,k),v in x.items() if si==i)
        supplier_util.append({"supplier_id":i,"used_units":used,"capacity_units":float(row.capacity_units),"utilisation_pct":100*used/float(row.capacity_units)})
    warehouse_util=[]
    for k,row in widx.iterrows():
        used=sum(val(v) for (i,wid),v in x.items() if wid==k)
        warehouse_util.append({"warehouse_id":k,"throughput_units":used,"capacity_units":float(row.capacity_units),"utilisation_pct":100*used/float(row.capacity_units)})
    route_metrics=[]
    for (i,k),v in x.items():
        route_metrics.append({"route":f"{i}->{k}","flow_units":val(v),"capacity_units":float(inbound[i,k].capacity_units),"slack_units":float(inbound[i,k].capacity_units)-val(v),"type":"inbound"})
    for (k,j),v in y.items():
        cap=float(outbound[k,j].capacity_units)
        route_metrics.append({"route":f"{k}->{j}","flow_units":val(v),"capacity_units":cap,"slack_units":cap-val(v),"type":"outbound"})
    return {"status":status,"solver_status_code":int(code),"objective_cost_inr":float(pulp.value(total_cost)),
            "objective_mode": objective_mode, "objective_value": float(pulp.value(model.objective)),
            "cost_breakdown":cost_parts,"inbound_allocations":inbound_alloc,"outbound_allocations":outbound_alloc,
            "supplier_utilisation":supplier_util,"warehouse_utilisation":warehouse_util,"route_metrics":route_metrics,
            "delivery":{"demand_weighted_average_outbound_hours":avg_delivery},
            "sustainability":{"inbound_emissions_kg_co2e":inbound_em,"outbound_emissions_kg_co2e":outbound_em,
                               "total_emissions_kg_co2e":inbound_em+outbound_em,"emissions_cap_kg":emissions_cap_kg},
            "total_demand_units":total_demand,"validation_warnings":report.warnings,
            "model_statistics":{"supplier_count":len(s),"warehouse_count":len(w),"customer_count":len(c),
                                 "inbound_route_count":len(ir),"outbound_route_count":len(oroutes),
                                 "decision_variable_count":len(x)+len(y),"constraint_count":len(model.constraints)}}


def solve_from_csv(data_dir: str | Path, emissions_cap_kg: float | None = None) -> dict:
    """Load canonical CSV tables and solve; returns a structured error if files fail."""
    from .data_validation import load_and_validate_csv_bundle
    tables, report=load_and_validate_csv_bundle(data_dir)
    if not report.is_valid:
        return {"status":"Invalid data","errors":report.errors,"warnings":report.warnings}
    return solve_network(tables, emissions_cap_kg=emissions_cap_kg)
