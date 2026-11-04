import json
from pathlib import Path
from supplychain.optimizer import solve_benchmark

result = solve_benchmark(Path(__file__).parent / "data/sample")
printable = {k:v for k,v in result.items() if k != "model"}
print(json.dumps(printable, indent=2))
