# Stage 7.1 — Multi-user authentication

## Included
- Registration with unique username and email.
- Login with username or email.
- Passwords stored as PBKDF2-HMAC-SHA256 hashes with random salts (310,000 iterations).
- Session-based login state managed by Streamlit.
- Logout.
- Per-user workspace persistence in SQLite (`data/app_users.db`).
- Each account has its own network tables, last optimisation, scenario and Pareto report.

## Run
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
Create an account from the registration tab, then sign in.

## Data location
The local SQLite database is created automatically at `data/app_users.db`.
Do not commit this file to Git. It contains account identifiers, password hashes and user workspace data.
The `.gitignore` should exclude `data/app_users.db`, `data/*.db`, and SQLite journal files.

## Security scope
This is a local prototype implementation, not a production identity system. For public deployment, use HTTPS and a managed identity provider (for example, Auth0, Microsoft Entra ID, or another OIDC provider), secure secrets, a managed database, rate limiting, account recovery, email verification, CSRF/session protections appropriate to the deployment, backups, and access-control testing. Do not expose the local SQLite database or deploy this implementation as a public multi-tenant service without a security review.
