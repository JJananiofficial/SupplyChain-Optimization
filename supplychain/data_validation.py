"""Structural and cross-table validation for supply-chain input datasets."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
import pandas as pd


REQUIRED_COLUMNS = {
    "suppliers": {"supplier_id", "name", "capacity_units", "purchase_price_inr_per_unit"},
    "warehouses": {"warehouse_id", "name", "capacity_units", "handling_cost_inr_per_unit"},
    "customers": {"customer_id", "name", "demand_units", "max_delivery_hours"},
    "inbound_routes": {"supplier_id", "warehouse_id", "transport_cost_inr_per_unit",
                       "capacity_units", "lead_time_hours", "emissions_kg_co2e_per_unit"},
    "outbound_routes": {"warehouse_id", "customer_id", "transport_cost_inr_per_unit",
                        "capacity_units", "lead_time_hours", "emissions_kg_co2e_per_unit"},
}

NUMERIC_RULES = {
    "suppliers": {
        "capacity_units": (0, True), "purchase_price_inr_per_unit": (0, True)
    },
    "warehouses": {
        "capacity_units": (0, True), "handling_cost_inr_per_unit": (0, True)
    },
    "customers": {
        "demand_units": (0, False), "max_delivery_hours": (0, False)
    },
    "inbound_routes": {
        "transport_cost_inr_per_unit": (0, True), "capacity_units": (0, True),
        "lead_time_hours": (0, False), "emissions_kg_co2e_per_unit": (0, True)
    },
    "outbound_routes": {
        "transport_cost_inr_per_unit": (0, True), "capacity_units": (0, True),
        "lead_time_hours": (0, False), "emissions_kg_co2e_per_unit": (0, True)
    },
}


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {"is_valid": self.is_valid, "errors": self.errors, "warnings": self.warnings}


def _check_table(name: str, df: pd.DataFrame, report: ValidationReport) -> None:
    missing = REQUIRED_COLUMNS[name] - set(df.columns)
    if missing:
        report.errors.append(f"{name}: missing required columns: {', '.join(sorted(missing))}")
        return

    id_columns = {
        "suppliers": ["supplier_id"],
        "warehouses": ["warehouse_id"],
        "customers": ["customer_id"],
        "inbound_routes": ["supplier_id", "warehouse_id"],
        "outbound_routes": ["warehouse_id", "customer_id"],
    }[name]

    if df.empty:
        report.errors.append(f"{name}: table must contain at least one row")
        return

    for col in id_columns:
        if df[col].isna().any() or (df[col].astype(str).str.strip() == "").any():
            report.errors.append(f"{name}.{col}: identifiers cannot be blank")

    if len(id_columns) == 1:
        if df[id_columns[0]].duplicated().any():
            report.errors.append(f"{name}: duplicate {id_columns[0]} values")
    elif df.duplicated(id_columns).any():
        report.errors.append(f"{name}: duplicate route pairs")

    for col, (minimum, strict) in NUMERIC_RULES[name].items():
        values = pd.to_numeric(df[col], errors="coerce")
        if values.isna().any():
            report.errors.append(f"{name}.{col}: values must be numeric and non-missing")
            continue
        if strict and (values < minimum).any():
            report.errors.append(f"{name}.{col}: values must be >= {minimum}")
        elif not strict and (values <= minimum).any():
            report.errors.append(f"{name}.{col}: values must be > {minimum}")


def validate_tables(tables: Mapping[str, pd.DataFrame], check_aggregate_capacity: bool = True) -> ValidationReport:
    """Validate required tables, values, references and basic network coverage.

    This performs data-quality and necessary-capacity checks. It is not a proof
    of LP feasibility; the optimisation solver remains the definitive test.
    """
    report = ValidationReport()
    missing_tables = set(REQUIRED_COLUMNS) - set(tables)
    if missing_tables:
        report.errors.append("Missing tables: " + ", ".join(sorted(missing_tables)))
        return report

    for name in REQUIRED_COLUMNS:
        _check_table(name, tables[name], report)

    if report.errors:
        return report

    s, w, c = tables["suppliers"], tables["warehouses"], tables["customers"]
    ir, oroutes = tables["inbound_routes"], tables["outbound_routes"]

    supplier_ids = set(s.supplier_id.astype(str))
    warehouse_ids = set(w.warehouse_id.astype(str))
    customer_ids = set(c.customer_id.astype(str))

    for row in ir.itertuples():
        if str(row.supplier_id) not in supplier_ids:
            report.errors.append(f"inbound_routes: unknown supplier_id {row.supplier_id}")
        if str(row.warehouse_id) not in warehouse_ids:
            report.errors.append(f"inbound_routes: unknown warehouse_id {row.warehouse_id}")
    for row in oroutes.itertuples():
        if str(row.warehouse_id) not in warehouse_ids:
            report.errors.append(f"outbound_routes: unknown warehouse_id {row.warehouse_id}")
        if str(row.customer_id) not in customer_ids:
            report.errors.append(f"outbound_routes: unknown customer_id {row.customer_id}")

    if report.errors:
        return report

    # Every warehouse in the data model must have at least one inbound and outbound arc.
    for wid in warehouse_ids:
        if not (ir.warehouse_id.astype(str) == wid).any():
            report.errors.append(f"warehouse {wid}: no inbound supplier route")
        if not (oroutes.warehouse_id.astype(str) == wid).any():
            report.errors.append(f"warehouse {wid}: no outbound customer route")

    # Every customer must have at least one route meeting its delivery window.
    max_delivery = c.set_index("customer_id")["max_delivery_hours"].to_dict()
    for cid in customer_ids:
        eligible = oroutes[
            (oroutes.customer_id.astype(str) == cid) &
            (pd.to_numeric(oroutes.lead_time_hours) <= float(max_delivery[cid]))
        ]
        if eligible.empty:
            report.errors.append(f"customer {cid}: no outbound route meets delivery window")

    total_supply = float(s.capacity_units.sum())
    total_demand = float(c.demand_units.sum())
    total_warehouse_capacity = float(w.capacity_units.sum())
    total_inbound_capacity = float(ir.capacity_units.sum())
    total_outbound_capacity = float(oroutes.capacity_units.sum())

    if check_aggregate_capacity:
        if total_supply < total_demand:
            report.errors.append("Aggregate supplier capacity is below total customer demand")
        if total_warehouse_capacity < total_demand:
            report.errors.append("Aggregate warehouse capacity is below total customer demand")
        if total_inbound_capacity < total_demand:
            report.errors.append("Aggregate inbound route capacity is below total customer demand")
        if total_outbound_capacity < total_demand:
            report.errors.append("Aggregate outbound route capacity is below total customer demand")

    if total_supply > total_demand:
        report.warnings.append(
            f"Aggregate supply exceeds demand by {total_supply - total_demand:g} units; "
            "unused supplier capacity is permitted."
        )
    return report


def load_and_validate_csv_bundle(data_dir: str | Path) -> tuple[dict[str, pd.DataFrame], ValidationReport]:
    """Load the five canonical CSV files and validate them."""
    base = Path(data_dir)
    tables = {}
    for name in REQUIRED_COLUMNS:
        path = base / f"{name}.csv"
        if not path.exists():
            report = ValidationReport(errors=[f"Missing input file: {path.name}"])
            return {}, report
        try:
            tables[name] = pd.read_csv(path)
        except Exception as exc:
            report = ValidationReport(errors=[f"Could not read {path.name}: {exc}"])
            return {}, report
    return tables, validate_tables(tables)
