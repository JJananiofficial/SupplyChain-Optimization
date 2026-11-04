import pandas as pd
import pytest
from pathlib import Path

from supplychain.data_validation import load_and_validate_csv_bundle
from supplychain.dynamic_optimizer import solve_network
from supplychain.scenario_analysis import apply_scenario, compare_results, run_scenario, run_price_sensitivity

ROOT = Path(__file__).resolve().parents[1]

def sample():
    tables, report = load_and_validate_csv_bundle(ROOT / "data" / "sample")
    assert report.is_valid, report.errors
    return tables

def test_price_shock_changes_only_target_supplier_price():
    tables = sample()
    changed = apply_scenario(tables, {"type": "supplier_price_shock", "supplier_id": "S1", "increase_pct": 10})
    assert changed["suppliers"].loc[changed["suppliers"].supplier_id == "S1", "purchase_price_inr_per_unit"].iloc[0] == pytest.approx(44)
    assert changed["suppliers"].loc[changed["suppliers"].supplier_id == "S2", "purchase_price_inr_per_unit"].iloc[0] == 43
    assert tables["suppliers"].loc[tables["suppliers"].supplier_id == "S1", "purchase_price_inr_per_unit"].iloc[0] == 40

def test_supplier_disruption_sets_supplier_and_inbound_route_capacity_zero():
    changed = apply_scenario(sample(), {"type": "supplier_disruption", "supplier_id": "S1"})
    assert changed["suppliers"].loc[changed["suppliers"].supplier_id == "S1", "capacity_units"].iloc[0] == 0
    assert (changed["inbound_routes"].loc[changed["inbound_routes"].supplier_id == "S1", "capacity_units"] == 0).all()

def test_demand_growth_scales_all_customer_demands():
    changed = apply_scenario(sample(), {"type": "demand_growth", "increase_pct": 20})
    assert changed["customers"]["demand_units"].sum() == pytest.approx(504)

def test_warehouse_capacity_reduction_is_applied():
    changed = apply_scenario(sample(), {"type": "warehouse_capacity_reduction", "warehouse_id": "W2", "reduction_pct": 25})
    cap = changed["warehouses"].loc[changed["warehouses"].warehouse_id == "W2", "capacity_units"].iloc[0]
    assert cap == pytest.approx(195)

def test_unknown_supplier_is_rejected():
    with pytest.raises(ValueError):
        apply_scenario(sample(), {"type": "supplier_price_shock", "supplier_id": "UNKNOWN", "increase_pct": 10})

def test_price_sensitivity_reoptimises_and_includes_baseline_point():
    rows = run_price_sensitivity(sample(), "S1", [0, 10])
    assert len(rows) == 2
    assert rows[0]["status"] == "Optimal"
    assert rows[0]["total_cost_inr"] == pytest.approx(22260, abs=1e-4)
    assert rows[1]["status"] == "Optimal"


def test_supplier_outage_is_reported_as_infeasible_not_invalid_data():
    tables = sample()
    run = run_scenario(tables, {
        "type": "supplier_disruption", "supplier_id": "S1"
    })
    assert run["result"]["status"] == "Infeasible"
    assert run["comparison"]["route_allocation_changes"] == []


def test_zero_capacity_is_allowed_for_disabled_supplier_and_route():
    changed = apply_scenario(sample(), {
        "type": "supplier_disruption", "supplier_id": "S1"
    })
    from supplychain.data_validation import validate_tables
    report = validate_tables(changed, check_aggregate_capacity=False)
    assert report.is_valid, report.errors
