"""Run cost-emissions Pareto analysis on a CSV dataset."""
import argparse, json
from pathlib import Path
from supplychain.data_validation import load_and_validate_csv_bundle
from supplychain.pareto_analysis import run_pareto_analysis, export_pareto_report

p=argparse.ArgumentParser(description="SupplyChain Optimizer — Cost-Emissions Pareto Analysis")
p.add_argument("--data", default="data/sample", help="Directory containing the five canonical CSV files")
p.add_argument("--points", type=int, default=11, help="Number of epsilon-constraint levels (2–101)")
p.add_argument("--output-dir", default="reports/pareto", help="Directory for JSON and CSV exports")
p.add_argument("--solver-msg", action="store_true", help="Show CBC solver logs")
a=p.parse_args()
tables, validation=load_and_validate_csv_bundle(Path(a.data))
if not validation.is_valid:
    result={"status":"Invalid data","errors":validation.errors,"warnings":validation.warnings}
else:
    result=run_pareto_analysis(tables, points=a.points, solver_msg=a.solver_msg)
if result.get("status")=="Completed":
    export_pareto_report(result, a.output_dir)
print(json.dumps(result, indent=2))
if result.get("status")!="Completed":
    raise SystemExit(1)
print(f"\nExports saved to: {Path(a.output_dir).resolve()}")
