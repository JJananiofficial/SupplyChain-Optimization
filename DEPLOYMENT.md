# Deploy SupplyChain Optimizer

## Local development

```powershell
py -3.15 -m pip install -r requirements.txt
py -3.15 -m streamlit run app.py
```

Local development uses SQLite at `data/app_users.db`, prototype username/password authentication, and a demo account. Do not expose the demo account publicly.

## Hosted deployment with OIDC and PostgreSQL

The hosted configuration uses Streamlit's built-in OpenID Connect support and a managed PostgreSQL database. The application stores a minimal identity record (issuer, subject, and available profile email) plus workspace data; it does not receive or authenticate users' OIDC passwords.

### Recommended low-friction services

For an initial deployment, use **Google as the OIDC provider** and **Supabase PostgreSQL** for workspace storage:

- Create a Supabase project and use its PostgreSQL connection string from the project dashboard. On Streamlit Community Cloud, prefer the provider's IPv4-compatible session pooler if the direct database endpoint is unreachable. Use the provider's TLS-required settings.
- Create an OAuth client in Google Cloud Console. Add `https://YOUR-APP-NAME.streamlit.app/oauth2callback` as an authorized redirect URI. Configure the OAuth consent screen and allowed users/audience appropriately.
- Use Google's OIDC discovery URL `https://accounts.google.com/.well-known/openid-configuration`.
- Put the client credentials and PostgreSQL URL into Streamlit Community Cloud's app secrets using the example below. Do not commit credentials.

The database and identity-provider selections are recommendations; use equivalents if you already have managed services.

1. Provision the database and OIDC client as described above.
2. Configure these values in Streamlit Community Cloud's secret store (do not commit secrets):

```toml
[auth]
redirect_uri = "https://YOUR-APP-URL/oauth2callback"
cookie_secret = "GENERATE-A-LONG-RANDOM-SECRET"
client_id = "YOUR-OIDC-CLIENT-ID"
client_secret = "YOUR-OIDC-CLIENT-SECRET"
server_metadata_url = "https://YOUR-PROVIDER/.well-known/openid-configuration"

[database]
url = "postgresql://APP_USER:URL_ENCODED_PASSWORD@DB_HOST:5432/DB_NAME?sslmode=require"

[deployment]
public_mode = true
```

3. Keep `public_mode = true` in the hosting secret store for the deployed app. Restrict sign-in to the intended users through the identity provider; enabling OIDC alone does not grant authorization policy.
4. Deploy `app.py`. The app creates its auth/workspace tables on startup. It will refuse to start in public mode if OIDC or PostgreSQL is missing.
5. Confirm OIDC login/logout, user isolation, workspace persistence after a restart, database backups, and access restrictions before inviting users.

### GitHub and Streamlit Community Cloud

1. Create a GitHub repository. The public source repository contains app code and synthetic sample data; never add real company/customer data, credentials, or database files.
2. Push this project to GitHub. The included GitHub Actions workflow runs tests for pushes and pull requests.
3. In Streamlit Community Cloud, create an app from the repository and select `app.py` as the entry point.
4. In the app settings, paste the OIDC, database, and `[deployment] public_mode = true` settings above. Deploy/redeploy after saving secrets.
5. Test sign-in, user-to-user workspace isolation, persistence after app restart, and authorization policy before sharing the public URL.

For PostgreSQL connection strings, use the provider's recommended TLS settings; prefer certificate and hostname verification (`sslmode=verify-full`) when the provider supports it. Never place credentials in source code, logs, screenshots, or this repository. Streamlit Community Cloud secrets can be entered in the app's settings without creating a local secrets file.

## Security and operations

- The password form and demo login are suppressed in public mode. New workspace identities are provisioned only after Streamlit's OIDC flow reports an authenticated user.
- OIDC itself does not restrict which accounts may sign in. Apply allowlists, tenant restrictions, or group policies at the identity provider and validate that policy in deployment.
- PostgreSQL is required for public mode. SQLite remains a local-development option only; it is not durable multi-replica or public deployment storage.
- The app stores workspaces as JSON in the database. Back up the database, test restore procedures, monitor database health, and set retention/access policies suitable for the data.
- Switching from local SQLite to PostgreSQL does not migrate existing accounts or workspaces. Back up and deliberately migrate any data you need; local password accounts must enroll through the configured identity provider.
- This change does not constitute a formal security audit. Before production, configure HTTPS at the hosting layer, review identity-provider policies, test authorization and recovery procedures, and have the deployment reviewed for your organization.

## Optional private-deployment settings

For non-public private deployments, these environment variables can customize local behavior:

- `SUPPLYCHAIN_DB_PATH`: SQLite file path (ignored when PostgreSQL is configured).
- `SUPPLYCHAIN_DATABASE_URL`: PostgreSQL connection string; alternatively set `[database].url` in Streamlit secrets.
- `SUPPLYCHAIN_ALLOW_SIGNUP=false`: disable local self-registration.
- `SUPPLYCHAIN_ALLOW_DEMO_LOGIN=false`: disable prototype demo access.
- `SUPPLYCHAIN_PUBLIC_MODE=true`: require both OIDC and PostgreSQL, and disable local sign-up/demo access. This can instead be set as `[deployment].public_mode = true` in Streamlit secrets.

Do not set public mode for a publicly reachable app until both managed OIDC and PostgreSQL are configured.
