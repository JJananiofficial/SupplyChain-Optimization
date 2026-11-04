from pathlib import Path
import pandas as pd
from supplychain.data_validation import load_and_validate_csv_bundle, validate_tables

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def test_sample_bundle_is_valid():
    tables, report = load_and_validate_csv_bundle(SAMPLE)
    assert report.is_valid, report.errors
    assert len(tables) == 5


def test_duplicate_supplier_id_is_rejected():
    tables = {name: df.copy() for name, df in load_and_validate_csv_bundle(SAMPLE)[0].items()}
    tables["suppliers"] = pd.concat([tables["suppliers"], tables["suppliers"].iloc[[0]]], ignore_index=True)
    report = validate_tables(tables)
    assert not report.is_valid
    assert any("duplicate supplier_id" in error for error in report.errors)


def test_unknown_supplier_reference_is_rejected():
    tables = {name: df.copy() for name, df in load_and_validate_csv_bundle(SAMPLE)[0].items()}
    tables["inbound_routes"].loc[0, "supplier_id"] = "UNKNOWN"
    report = validate_tables(tables)
    assert not report.is_valid
    assert any("unknown supplier_id" in error for error in report.errors)


def test_negative_transport_cost_is_rejected():
    tables = {name: df.copy() for name, df in load_and_validate_csv_bundle(SAMPLE)[0].items()}
    tables["outbound_routes"].loc[0, "transport_cost_inr_per_unit"] = -1
    report = validate_tables(tables)
    assert not report.is_valid
    assert any("transport_cost_inr_per_unit" in error for error in report.errors)


def test_insufficient_aggregate_supply_is_rejected():
    tables = {name: df.copy() for name, df in load_and_validate_csv_bundle(SAMPLE)[0].items()}
    tables["suppliers"].loc[:, "capacity_units"] = [100, 100, 100]
    report = validate_tables(tables)
    assert not report.is_valid
    assert any("Aggregate supplier capacity" in error for error in report.errors)


def test_customer_without_eligible_delivery_route_is_rejected():
    tables = {name: df.copy() for name, df in load_and_validate_csv_bundle(SAMPLE)[0].items()}
    tables["outbound_routes"].loc[
        tables["outbound_routes"]["customer_id"] == "C1", "lead_time_hours"
    ] = 100
    report = validate_tables(tables)
    assert not report.is_valid
    assert any("no outbound route meets delivery window" in error for error in report.errors)
