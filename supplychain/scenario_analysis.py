"""Scenario analysis and sensitivity tools for the SupplyChain Optimizer.

Each scenario copies and modifies the input tables, then re-solves the LP.
Baseline results are never mutated.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
import pandas as pd

from .dynamic_optimizer import solve_network


def _result_cost(result: Mapping[str, Any]) -> float | None:
    value = result.get("objective_cost_inr")
    return None if value is None else float(value)


def _allocation_map(result: Mapping[str, Any]) -> dict[str, float]:
    allocations: dict[str, float] = {}
    for item in result.get("inbound_allocations", []):
        key = f"{item['supplier_id']}->{item['warehouse_id']}"
        allocations[key] = float(item["units"])
    for item in result.get("outbound_allocations", []):
        key = f"{item['warehouse_id']}->{item['customer_id']}"
        allocations[key] = float(item["units"])
    return allocations


def compare_results(baseline: Mapping[str, Any], scenario: Mapping[str, Any]) -> dict[str, Any]:
    """Return comparable KPIs and route-level allocation changes."""
    base_cost = _result_cost(baseline)
    scenario_cost = _result_cost(scenario)
    base_emissions = baseline.get("sustainability", {}).get("total_emissions_kg_co2e")
    scenario_emissions = scenario.get("sustainability", {}).get("total_emissions_kg_co2e")
    base_delivery = baseline.get("delivery", {}).get("demand_weighted_average_outbound_hours")
    scenario_delivery = scenario.get("delivery", {}).get("demand_weighted_average_outbound_hours")

    def delta(new: Any, old: Any) -> float | None:
        if new is None or old is None:
            return None
        return float(new) - float(old)

    # Never interpret a failed/infeasible solve as zero flow on every route.
    if scenario.get("status") != "Optimal":
        route_changes = []
    else:
        base_alloc = _allocation_map(baseline)
        scen_alloc = _allocation_map(scenario)
        route_changes = []
        for route in sorted(set(base_alloc) | set(scen_alloc)):
            before, after = base_alloc.get(route, 0.0), scen_alloc.get(route, 0.0)
            if abs(after - before) > 1e-7:
                route_changes.append({
                    "route": route,
                    "baseline_units": before,
                    "scenario_units": after,
                    "change_units": after - before,
                })

    return {
        "baseline_status": baseline.get("status"),
        "scenario_status": scenario.get("status"),
        "baseline_cost_inr": base_cost,
        "scenario_cost_inr": scenario_cost,
        "cost_change_inr": delta(scenario_cost, base_cost),
        "cost_change_pct": (
            100.0 * (scenario_cost - base_cost) / base_cost
            if base_cost not in (None, 0) and scenario_cost is not None else None
        ),
        "baseline_emissions_kg_co2e": base_emissions,
        "scenario_emissions_kg_co2e": scenario_emissions,
        "emissions_change_kg_co2e": delta(scenario_emissions, base_emissions),
        "baseline_average_delivery_hours": base_delivery,
        "scenario_average_delivery_hours": scenario_delivery,
        "delivery_change_hours": delta(scenario_delivery, base_delivery),
        "route_allocation_changes": route_changes,
    }




def apply_scenario(tables: Mapping[str, pd.DataFrame], scenario: Mapping[str, Any]) -> dict[str, pd.DataFrame]:
    """Create modified copies of canonical tables for a supported scenario."""
    changed = {name: frame.copy(deep=True) for name, frame in tables.items()}
    kind = scenario.get("type")

    if kind == "supplier_price_shock":
        supplier_id = str(scenario["supplier_id"])
        pct = float(scenario["increase_pct"])
        if pct < -100:
            raise ValueError("increase_pct cannot be less than -100.")
        mask = changed["suppliers"]["supplier_id"].astype(str) == supplier_id
        if not mask.any():
            raise ValueError(f"Unknown supplier_id: {supplier_id}")
        changed["suppliers"].loc[mask, "purchase_price_inr_per_unit"] *= (1 + pct / 100)

    elif kind == "supplier_disruption":
        supplier_id = str(scenario["supplier_id"])
        mask = changed["suppliers"]["supplier_id"].astype(str) == supplier_id
        if not mask.any():
            raise ValueError(f"Unknown supplier_id: {supplier_id}")
        changed["suppliers"].loc[mask, "capacity_units"] = 0
        # Route capacities are also set to zero to represent a complete outage.
        route_mask = changed["inbound_routes"]["supplier_id"].astype(str) == supplier_id
        changed["inbound_routes"].loc[route_mask, "capacity_units"] = 0

    elif kind == "demand_growth":
        pct = float(scenario["increase_pct"])
        if pct < -100:
            raise ValueError("increase_pct cannot be less than -100.")
        changed["customers"]["demand_units"] *= (1 + pct / 100)

    elif kind == "warehouse_capacity_reduction":
        warehouse_id = str(scenario["warehouse_id"])
        pct = float(scenario["reduction_pct"])
        if not 0 <= pct <= 100:
            raise ValueError("reduction_pct must be between 0 and 100.")
        mask = changed["warehouses"]["warehouse_id"].astype(str) == warehouse_id
        if not mask.any():
            raise ValueError(f"Unknown warehouse_id: {warehouse_id}")
        changed["warehouses"].loc[mask, "capacity_units"] *= (1 - pct / 100)

    else:
        raise ValueError(f"Unsupported scenario type: {kind}")

    return changed


def run_scenario(
    tables: Mapping[str, pd.DataFrame],
    scenario: Mapping[str, Any],
    baseline_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply one scenario, re-solve the LP, and compare with baseline."""
    baseline = baseline_result or solve_network(tables)
    changed = apply_scenario(tables, scenario)
    carbon_cap = scenario.get("emissions_cap_kg")
    result = solve_network(changed, emissions_cap_kg=carbon_cap, scenario_mode=True)
    return {
        "scenario": dict(scenario),
        "result": result,
        "comparison": compare_results(baseline, result),
    }


def run_standard_scenarios(tables: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    """Run the project's predefined management stress tests."""
    baseline = solve_network(tables)
    if baseline.get("status") != "Optimal":
        return {"baseline": baseline, "scenarios": [], "error": "Baseline must be Optimal before scenario analysis."}

    definitions = [
        {"name": "S1 purchase price +10%", "type": "supplier_price_shock", "supplier_id": "S1", "increase_pct": 10},
        {"name": "S1 supplier outage", "type": "supplier_disruption", "supplier_id": "S1"},
        {"name": "Demand growth +20%", "type": "demand_growth", "increase_pct": 20},
        {"name": "W2 capacity reduction -25%", "type": "warehouse_capacity_reduction", "warehouse_id": "W2", "reduction_pct": 25},
        {"name": "Carbon cap 1,200 kg", "type": "carbon_cap", "emissions_cap_kg": 1200},
    ]

    outputs = []
    for definition in definitions:
        if definition["type"] == "carbon_cap":
            changed = {name: frame.copy(deep=True) for name, frame in tables.items()}
            result = solve_network(changed, emissions_cap_kg=definition["emissions_cap_kg"], scenario_mode=True)
            outputs.append({
                "scenario": definition,
                "result": result,
                "comparison": compare_results(baseline, result),
            })
        else:
            outputs.append(run_scenario(tables, definition, baseline))
    return {"baseline": baseline, "scenarios": outputs}


def run_price_sensitivity(
    tables: Mapping[str, pd.DataFrame],
    supplier_id: str,
    increases_pct: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Re-optimise over a supplier price-shock grid."""
    baseline = solve_network(tables)
    if baseline.get("status") != "Optimal":
        raise ValueError("Baseline must be Optimal before sensitivity analysis.")
    grid = increases_pct if increases_pct is not None else [0, 5, 10, 15, 20]
    rows = []
    for pct in grid:
        scenario = {
            "name": f"{supplier_id} price +{pct:g}%",
            "type": "supplier_price_shock",
            "supplier_id": supplier_id,
            "increase_pct": float(pct),
        }
        run = run_scenario(tables, scenario, baseline)
        comparison = run["comparison"]
        rows.append({
            "supplier_id": supplier_id,
            "price_increase_pct": float(pct),
            "status": run["result"].get("status"),
            "total_cost_inr": run["result"].get("objective_cost_inr"),
            "cost_change_inr": comparison["cost_change_inr"],
            "cost_change_pct": comparison["cost_change_pct"],
            "total_emissions_kg_co2e": run["result"].get("sustainability", {}).get("total_emissions_kg_co2e"),
            "average_delivery_hours": run["result"].get("delivery", {}).get("demand_weighted_average_outbound_hours"),
            "route_allocation_changes": comparison["route_allocation_changes"],
        })
    return rows
