"""Cost-emissions Pareto analysis using the epsilon-constraint method."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .dynamic_optimizer import solve_network


def _is_dominated(point, others, tol=1e-7):
    """A point is dominated if another is no worse in cost and emissions and better in one."""
    for other in others:
        if other is point:
            continue
        no_worse = (other["cost_inr"] <= point["cost_inr"] + tol and
                    other["emissions_kg_co2e"] <= point["emissions_kg_co2e"] + tol)
        strictly_better = (other["cost_inr"] < point["cost_inr"] - tol or
                           other["emissions_kg_co2e"] < point["emissions_kg_co2e"] - tol)
        if no_worse and strictly_better:
            return True
    return False


def run_pareto_analysis(tables, points: int = 11, solver_msg: bool = False) -> dict:
    """Find min-emissions and min-cost endpoints, then solve a cap sweep.

    `points` is the requested number of evenly spaced epsilon caps including
    both endpoints. The actual non-dominated set is computed from feasible
    solutions, not assumed from the cap order.
    """
    if not isinstance(points, int) or points < 2 or points > 101:
        return {"status": "Invalid data", "errors": ["points must be an integer from 2 to 101"]}

    min_em = solve_network(tables, solver_msg=solver_msg, scenario_mode=True, objective_mode="emissions")
    if min_em.get("status") != "Optimal":
        return {"status": min_em.get("status", "Error"), "diagnostic": "Could not find a feasible minimum-emissions solution.", "minimum_emissions_result": min_em}
    min_cost = solve_network(tables, solver_msg=solver_msg, scenario_mode=True, objective_mode="cost")
    if min_cost.get("status") != "Optimal":
        return {"status": min_cost.get("status", "Error"), "diagnostic": "Could not find a feasible minimum-cost solution.", "minimum_cost_result": min_cost}

    low = float(min_em["sustainability"]["total_emissions_kg_co2e"])
    high = float(min_cost["sustainability"]["total_emissions_kg_co2e"])
    if high < low - 1e-6:
        return {"status": "Error", "diagnostic": "Endpoint inconsistency: cost-optimal emissions are below minimum-emissions endpoint."}
    caps = sorted(set(round(low + (high-low)*i/(points-1), 8) for i in range(points)))
    if len(caps) == 1:
        caps = [caps[0], caps[0]]

    records=[]
    for cap in caps:
        result=solve_network(tables, emissions_cap_kg=cap, solver_msg=solver_msg, scenario_mode=True)
        if result.get("status") == "Optimal":
            records.append({
                "emissions_cap_kg_co2e": cap,
                "status": "Optimal",
                "cost_inr": float(result["objective_cost_inr"]),
                "emissions_kg_co2e": float(result["sustainability"]["total_emissions_kg_co2e"]),
                "average_delivery_hours": float(result["delivery"]["demand_weighted_average_outbound_hours"]),
                "inbound_allocations": result["inbound_allocations"],
                "outbound_allocations": result["outbound_allocations"],
            })
        else:
            records.append({"emissions_cap_kg_co2e": cap, "status": result.get("status", "Error"),
                            "cost_inr": None, "emissions_kg_co2e": None,
                            "average_delivery_hours": None, "diagnostic": result.get("diagnostic")})

    feasible=[r for r in records if r["status"] == "Optimal"]
    frontier=[r for r in feasible if not _is_dominated(r, feasible)]
    frontier.sort(key=lambda r: (r["emissions_kg_co2e"], r["cost_inr"]))
    return {
        "status": "Completed",
        "method": "epsilon-constraint",
        "objective_description": "Minimise total operating cost subject to a maximum total CO2e emissions limit.",
        "minimum_emissions_kg_co2e": low,
        "minimum_emissions_solution_cost_inr": float(min_em["objective_cost_inr"]),
        "minimum_cost_inr": float(min_cost["objective_cost_inr"]),
        "minimum_cost_solution_emissions_kg_co2e": high,
        "requested_points": points,
        "feasible_solution_count": len(feasible),
        "frontier_point_count": len(frontier),
        "sweep": records,
        "pareto_frontier": frontier,
    }


def export_pareto_report(report: dict, output_dir: str | Path) -> None:
    """Export JSON and CSV (including feasible sweep and frontier)."""
    out=Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    (out/"pareto_analysis.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    rows=[]
    for r in report.get("sweep", []):
        rows.append({k:r.get(k) for k in ("emissions_cap_kg_co2e","status","cost_inr","emissions_kg_co2e","average_delivery_hours")})
    pd.DataFrame(rows).to_csv(out/"pareto_sweep.csv", index=False)
    frontier=[]
    for r in report.get("pareto_frontier", []):
        frontier.append({k:r.get(k) for k in ("emissions_cap_kg_co2e","cost_inr","emissions_kg_co2e","average_delivery_hours")})
    pd.DataFrame(frontier).to_csv(out/"pareto_frontier.csv", index=False)
