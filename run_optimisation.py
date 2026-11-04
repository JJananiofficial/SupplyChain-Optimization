"""Run the dynamic optimiser against a CSV dataset."""
import argparse, json
from pathlib import Path
from supplychain.dynamic_optimizer import solve_from_csv

p=argparse.ArgumentParser(description="Dynamic SupplyChain Optimizer")
p.add_argument("--data",default="data/sample",help="Directory containing the five canonical CSV files")
p.add_argument("--emissions-cap",type=float,default=None,help="Optional kg CO2e cap (epsilon constraint)")
p.add_argument("--output",default=None,help="Optional JSON output file")
a=p.parse_args()
result=solve_from_csv(Path(a.data),a.emissions_cap)
rendered=json.dumps(result,indent=2)
print(rendered)
if a.output: Path(a.output).write_text(rendered+"\n",encoding="utf-8")
