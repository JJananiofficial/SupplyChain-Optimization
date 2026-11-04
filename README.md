# SupplyChain Optimizer

A Streamlit-based multi-user supply-chain decision-support application.

## Run
```bash
py -3.15 -m pip install -r requirements.txt
py -3.15 -m streamlit run app.py
```

For local development, the demo login is `planner_demo` / `demo12345`, or create an account. Demo access is disabled in public mode.

## Deployment-ready usability notes
- Use the sample dataset or upload the five canonical CSV files.
- Validate the network before running the optimiser.
- Reset to the sample network with one click if the current data becomes messy.
- Each signed-in user keeps a separate local workspace in SQLite.
- This is suitable for internal/private deployment; public deployment should use a managed identity provider and database.

Features include multi-echelon network data management, CSV templates, validation, linear-programming optimisation, scenario analysis, sustainability and Pareto analysis, exports, and per-user workspace persistence.

See `DEPLOYMENT.md` for hosted deployment with OIDC and managed PostgreSQL, plus configuration and security requirements. Public mode intentionally refuses to start without both services configured.
