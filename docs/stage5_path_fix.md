# Stage 5 path fix

The scenario runner now resolves its default sample data and report directory relative to `run_scenarios.py`, not the terminal's current working directory. This prevents `Missing input file: suppliers.csv` when the script is launched from a different directory.

Run from the project folder:

```bash
python run_scenarios.py --price-sensitivity
```

You can also launch it from another directory using the full path to `run_scenarios.py`; the default sample data path will still resolve correctly.
