from pathlib import Path
import pandas as pd
from supplychain.pareto_analysis import run_pareto_analysis, _is_dominated

DATA=Path(__file__).resolve().parents[1]/"data"/"sample"
def load_tables():
    return {name:pd.read_csv(DATA/f"{name}.csv") for name in ("suppliers","warehouses","customers","inbound_routes","outbound_routes")}

def test_pareto_analysis_has_valid_endpoints_and_frontier():
    report=run_pareto_analysis(load_tables(), points=5)
    assert report["status"]=="Completed"
    assert report["minimum_emissions_kg_co2e"] <= report["minimum_cost_solution_emissions_kg_co2e"]
    assert report["feasible_solution_count"] >= 1
    assert report["frontier_point_count"] >= 1
    for point in report["pareto_frontier"]:
        assert point["status"]=="Optimal"

def test_dominated_point_detection():
    a={"cost_inr":100,"emissions_kg_co2e":50}
    b={"cost_inr":90,"emissions_kg_co2e":40}
    assert _is_dominated(a,[a,b])
    assert not _is_dominated(b,[a,b])

def test_invalid_point_count():
    report=run_pareto_analysis(load_tables(), points=1)
    assert report["status"]=="Invalid data"
