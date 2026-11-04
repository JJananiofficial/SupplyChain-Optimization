"""Run the standard Stage 5 scenario suite and save a JSON report."""
import argparse
import json
from pathlib import Path

from supplychain.data_validation import load_and_validate_csv_bundle
from supplychain.scenario_analysis import run_standard_scenarios, run_price_sensitivity

parser = argparse.ArgumentParser(description="Stage 5 scenario and sensitivity analysis")
PROJECT_DIR = Path(__file__).resolve().parent
parser.add_argument("--data", default=str(PROJECT_DIR / "data" / "sample"),
                    help="Directory containing the five canonical CSV files")
parser.add_argument("--output", default=str(PROJECT_DIR / "reports" / "stage5_scenarios.json"),
                    help="JSON report path")
parser.add_argument("--price-sensitivity", action="store_true", help="Also run S1 price sensitivity at 0, 5, 10, 15 and 20 percent")
args = parser.parse_args()

data_dir = Path(args.data).expanduser().resolve()
tables, validation = load_and_validate_csv_bundle(data_dir)
if not validation.is_valid:
    payload = {"status": "Invalid data", "errors": validation.errors, "warnings": validation.warnings}
else:
    payload = run_standard_scenarios(tables)
    if args.price_sensitivity and payload.get("baseline", {}).get("status") == "Optimal":
        payload["s1_price_sensitivity"] = run_price_sensitivity(tables, "S1")

out = Path(args.output).expanduser()
if not out.is_absolute():
    out = PROJECT_DIR / out
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
print(f"\nSaved report: {out}")
