# Stage 7 — Decision-Support Dashboard

## Run locally

From the `SupplyChainOptimizer` project root:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit prints a local URL (normally `http://localhost:8501`). Open it in a browser.
On Windows, `run_dashboard.bat` launches the dashboard from any working directory.
Do not use the editor's plain Python file runner (`python app.py`), which runs
outside Streamlit's script runtime and produces `missing ScriptRunContext` warnings.

## Modules

- **Overview:** network size, readiness and model summary.
- **Network & data:** upload the five canonical CSV tables, edit rows, download templates and validate inputs.
- **Optimisation:** run the dynamic cost-minimising LP with an optional emissions cap; inspect allocations, cost breakdown, utilisation and route slack.
- **Scenario laboratory:** run supplier price shocks, supplier outages, demand growth, warehouse capacity reductions and carbon-cap tests.
- **Sustainability & Pareto:** calculate minimum-emissions and minimum-cost endpoints, perform an epsilon-constraint sweep and inspect/export the non-dominated frontier.
- **Exports & methodology:** model formulation, assumptions, limitations and reproducibility downloads.

## Data tables

The app expects five CSV tables named `suppliers.csv`, `warehouses.csv`, `customers.csv`, `inbound_routes.csv`, and `outbound_routes.csv`. Their required columns are defined in `supplychain/data_validation.py`; downloadable blank templates are in `data/templates/`.

## Design notes

The interface calls the existing `supplychain` modules directly. Optimisation logic remains outside the UI layer. Session state retains edited tables and the most recent outputs for the current browser session. Uploaded datasets replace all five tables together to prevent accidental mixing of datasets.

## Important limitations

This is a research prototype, not a production ERP or transport execution system. It models deterministic single-period continuous flows for one interchangeable product. Synthetic sample values and emissions factors are illustrative. LP feasibility and optimality are conditional on the supplied data and assumptions. The dashboard does not model inventory over time, vehicle routing, integer shipment quantities, uncertainty, or multi-product shared capacity.
