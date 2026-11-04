import json
from pathlib import Path
import pytest

pulp = pytest.importorskip("pulp")
from supplychain.optimizer import solve_benchmark

ROOT = Path(__file__).resolve().parents[1]

def test_benchmark_objective_matches_reference():
    expected = json.loads((ROOT / "data/benchmark/expected_results.json").read_text())
    result = solve_benchmark(ROOT / "data/sample")
    assert result["status"] == "Optimal"
    assert result["objective_cost_inr"] == pytest.approx(expected["objective_cost_inr"], abs=1e-5)

def test_benchmark_allocations_match_reference():
    expected = json.loads((ROOT / "data/benchmark/expected_results.json").read_text())
    result = solve_benchmark(ROOT / "data/sample")
    for route, quantity in expected["inbound_allocation_units"].items():
        assert result["inbound"][route] == pytest.approx(quantity, abs=1e-5)
    for route, quantity in expected["outbound_allocation_units"].items():
        assert result["outbound"][route] == pytest.approx(quantity, abs=1e-5)

def test_all_customer_demands_are_fulfilled():
    result = solve_benchmark(ROOT / "data/sample")
    assert sum(result["outbound"].get(f"W1->C{j}", 0) +
               result["outbound"].get(f"W2->C{j}", 0) for j in range(1,5)) == pytest.approx(420)

def test_warehouse_flow_is_conserved():
    result = solve_benchmark(ROOT / "data/sample")
    for warehouse in ["W1", "W2"]:
        inbound_total = sum(v for k,v in result["inbound"].items() if k.endswith("->"+warehouse))
        outbound_total = sum(v for k,v in result["outbound"].items() if k.startswith(warehouse+"->"))
        assert inbound_total == pytest.approx(outbound_total)

def test_all_allocations_are_nonnegative():
    result = solve_benchmark(ROOT / "data/sample")
    assert all(v >= -1e-8 for v in result["inbound"].values())
    assert all(v >= -1e-8 for v in result["outbound"].values())
