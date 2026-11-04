"""SupplyChain Optimizer — Streamlit decision-support interface.

Run from the project root with: python -m streamlit run app.py
Do not run with `python app.py`; Streamlit must manage the script runtime.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supplychain.data_validation import REQUIRED_COLUMNS, validate_tables  # noqa: E402
from supplychain.dynamic_optimizer import solve_network  # noqa: E402
from supplychain.scenario_analysis import run_scenario  # noqa: E402
from supplychain.pareto_analysis import run_pareto_analysis  # noqa: E402
from supplychain.auth import (  # noqa: E402
    get_auth_config,
    configure_database,
    configure_public_mode,
    init_auth_db,
    register_user,
    authenticate_user,
    provision_oidc_user,
    save_workspace,
    load_workspace,
)

TABLE_NAMES = list(REQUIRED_COLUMNS)
TABLE_LABELS = {
    "suppliers": "Suppliers",
    "warehouses": "Warehouses",
    "customers": "Customers",
    "inbound_routes": "Inbound routes",
    "outbound_routes": "Outbound routes",
}

st.set_page_config(
    page_title="SupplyChain Optimizer",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --pine:#183D32; --pine2:#245545; --moss:#6F8D68; --sage:#DCE7D8; --clay:#C8794A; --sand:#F3EFE6; --paper:#FBFAF6; --ink:#26352E; --muted:#718078; --line:#E2E5DC; }
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:var(--sand);color:var(--ink)}
.block-container{padding:1.6rem 2.3rem 3rem;max-width:1600px}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#173B31 0%,#204B3D 68%,#183D32 100%);border-right:1px solid rgba(255,255,255,.08)}
[data-testid="stSidebar"] *{color:#F4F2E9!important}
[data-testid="stSidebar"] .stButton>button,[data-testid="stSidebar"] .stDownloadButton>button{color:#183D32!important;background:#FBFAF6;border-color:#FBFAF6}
[data-testid="stSidebar"] .stButton>button:hover,[data-testid="stSidebar"] .stDownloadButton>button:hover{color:#183D32!important;background:#DCE7D8;border-color:#DCE7D8}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.48rem .65rem;border-radius:9px;margin:.12rem 0}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(255,255,255,.10)}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"]{gap:.12rem}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.18)}
.brand-mark{font-family:Manrope,sans-serif;font-weight:800;letter-spacing:-.04em;font-size:1.25rem;line-height:1.15;color:#FFFDF5}
.brand-sub{color:#C6D5C8;font-size:.76rem;line-height:1.45;margin-top:.45rem}
.side-kicker{color:#B9CDBD;font-size:.66rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.page-head{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:1.25rem 1.55rem;margin:.2rem 0 1.35rem;display:flex;justify-content:space-between;align-items:center;gap:1rem;box-shadow:0 5px 18px rgba(32,59,46,.035)}
.page-kicker{color:var(--clay);text-transform:uppercase;letter-spacing:.15em;font-size:.67rem;font-weight:800;margin-bottom:.35rem}
.page-title{font-family:Manrope,sans-serif;font-size:1.85rem;line-height:1.15;font-weight:800;letter-spacing:-.045em;color:var(--pine);margin:0}
.page-desc{color:var(--muted);font-size:.91rem;margin-top:.4rem}
.status-pill{background:var(--sage);color:var(--pine);padding:.45rem .8rem;border-radius:999px;font-size:.75rem;font-weight:700;white-space:nowrap}
.section-eyebrow{color:var(--clay);font-size:.67rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;margin:.4rem 0 .2rem}
h1,h2,h3{font-family:Manrope,sans-serif!important;color:var(--pine)!important;letter-spacing:-.035em!important}
h2{font-size:1.35rem!important} h3{font-size:1.08rem!important}
[data-testid="stMetric"]{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:1rem 1.05rem;box-shadow:0 4px 14px rgba(32,59,46,.035)}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:.78rem!important}
[data-testid="stMetricValue"]{color:var(--pine)!important;font-family:Manrope,sans-serif}
[data-testid="stMetricDelta"]{font-size:.76rem}
.stButton>button,.stDownloadButton>button{border-radius:9px;border:1px solid var(--pine);background:var(--pine);color:#FFFDF5;font-weight:700;padding:.52rem 1rem;transition:all .15s ease}
.stButton>button:hover,.stDownloadButton>button:hover{background:var(--pine2);border-color:var(--pine2);color:white;transform:translateY(-1px)}
.stButton>button[kind="secondary"]{background:var(--paper);color:var(--pine)}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
[data-testid="stExpander"]{background:var(--paper);border:1px solid var(--line);border-radius:12px}
[data-baseweb="tab-list"]{gap:.35rem}
button[data-baseweb="tab"]{border-radius:8px 8px 0 0}
.stTabs [aria-selected="true"]{color:var(--pine)!important;border-bottom-color:var(--clay)!important}
.section-note{color:var(--muted);font-size:.9rem}
div[data-testid="stAlert"]{border-radius:11px}
[data-testid="stPlotlyChart"]{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:.45rem}
@media(max-width:900px){.block-container{padding:1rem 1rem 2rem}.page-head{align-items:flex-start;flex-direction:column}}

.auth-story{background:linear-gradient(150deg,#173B31,#285A46);padding:2.7rem 2.2rem;color:#F7F5EC;border-radius:20px;min-height:535px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 16px 40px rgba(24,61,50,.12)}
.auth-story h1{color:#FFFDF5!important;font-family:Manrope,sans-serif!important;font-size:2.15rem!important;line-height:1.12!important}
.auth-story p{color:#D2DFD3!important;font-size:.96rem;line-height:1.7}
.auth-kicker{color:#C8794A!important;font-size:.68rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.auth-feature{border-top:1px solid rgba(255,255,255,.18);padding-top:.9rem;margin-top:.9rem;color:#D8E4D9!important;font-size:.82rem}
.auth-screen [data-testid="stHorizontalBlock"]{align-items:stretch;gap:1.1rem}
.auth-screen [data-testid="column"]:first-child{padding:0}
.auth-screen [data-testid="column"]:last-child{background:#FBFAF6;border:1px solid #E2E5DC;border-radius:20px;padding:2rem 2rem 1.4rem;box-shadow:0 16px 40px rgba(24,61,50,.07)}
.auth-screen [data-testid="stWidgetLabel"] p,.auth-screen label{color:#26352E!important}
.auth-screen input{color:#26352E!important;background:#FFFFFF!important}
.auth-screen input::placeholder{color:#89958D!important}
.auth-screen [data-baseweb="radio"] label{color:#26352E!important}
.auth-screen [data-testid="stForm"]{background:#FFFFFF;border:1px solid #E2E5DC;border-radius:14px;padding:1rem}
.auth-screen [data-testid="stCaptionContainer"]{color:#718078!important}
@media(max-width:760px){.auth-story{min-height:300px;padding:1.7rem}.auth-screen [data-testid="column"]:last-child{padding:1.3rem}}

</style>
""", unsafe_allow_html=True)


def load_sample_tables() -> dict[str, pd.DataFrame]:
    sample_dir = ROOT / "data" / "sample"
    return {name: pd.read_csv(sample_dir / f"{name}.csv") for name in TABLE_NAMES}


def init_state() -> None:
    if "sc_tables" not in st.session_state:
        st.session_state.sc_tables = load_sample_tables()
    if "sc_result" not in st.session_state:
        st.session_state.sc_result = None
    if "sc_pareto" not in st.session_state:
        st.session_state.sc_pareto = None
    if "sc_scenario" not in st.session_state:
        st.session_state.sc_scenario = None


def reset_workspace_to_sample() -> None:
    st.session_state.sc_tables = load_sample_tables()
    st.session_state.sc_result = None
    st.session_state.sc_pareto = None
    st.session_state.sc_scenario = None
    if "sc_user" in st.session_state:
        save_workspace(st.session_state["sc_user"]["id"], {
            "tables": {name: st.session_state.sc_tables[name].to_dict(orient="records") for name in TABLE_NAMES},
            "result": None,
            "pareto": None,
            "scenario": None,
        })


def money(value: Any) -> str:
    return "—" if value is None else f"₹{float(value):,.2f}"


def show_validation(tables: dict[str, pd.DataFrame]) -> bool:
    report = validate_tables(tables)
    if report.errors:
        st.error("Input validation failed. Resolve the following issues before optimisation.")
        for item in report.errors:
            st.write(f"- {item}")
        return False
    st.success("All five input tables passed structural and cross-reference validation.")
    for item in report.warnings:
        st.warning(item)
    return True


def result_kpis(result: dict) -> None:
    if result.get("status") != "Optimal":
        st.error(f"Solver status: {result.get('status', 'Unknown')}")
        if result.get("diagnostic"):
            st.info(result["diagnostic"])
        for error in result.get("errors", []):
            st.write(f"- {error}")
        return
    cost = result["objective_cost_inr"]
    emissions = result["sustainability"]["total_emissions_kg_co2e"]
    delivery = result["delivery"]["demand_weighted_average_outbound_hours"]
    a, b, c, d = st.columns(4)
    a.metric("Optimised operating cost", money(cost))
    b.metric("Total emissions", f"{emissions:,.1f} kg CO₂e")
    c.metric("Avg. outbound delivery", f"{delivery:,.2f} hours")
    d.metric("Demand fulfilled", f"{result['total_demand_units']:,.0f} units")


def allocations_frame(result: dict) -> pd.DataFrame:
    rows = []
    for row in result.get("inbound_allocations", []):
        rows.append({"Stage": "Inbound", "Origin": row["supplier_id"], "Destination": row["warehouse_id"], "Units": row["units"]})
    for row in result.get("outbound_allocations", []):
        rows.append({"Stage": "Outbound", "Origin": row["warehouse_id"], "Destination": row["customer_id"], "Units": row["units"]})
    return pd.DataFrame(rows, columns=["Stage", "Origin", "Destination", "Units"])


def configure_auth_from_secrets() -> bool:
    try:
        database_settings = st.secrets.get("database", {})
        auth_settings = st.secrets.get("auth", {})
        deployment_settings = st.secrets.get("deployment", {})
    except st.errors.StreamlitSecretNotFoundError:
        return False
    configure_database(database_settings.get("url"))
    public_setting = deployment_settings.get("public_mode")
    if isinstance(public_setting, str):
        public_setting = public_setting.strip().lower() in {"1", "true", "yes", "on"}
    configure_public_mode(public_setting if isinstance(public_setting, bool) else None)
    required_oidc_settings = ("client_id", "client_secret", "server_metadata_url", "redirect_uri", "cookie_secret")
    return all(auth_settings.get(key) for key in required_oidc_settings)


def current_oidc_identity() -> dict[str, str] | None:
    if not st.user.is_logged_in:
        return None
    claims = st.user.to_dict()
    auth_settings = st.secrets["auth"]
    issuer = claims.get("iss") or auth_settings.get("server_metadata_url", "configured-oidc-provider")
    subject = claims.get("sub")
    if not subject:
        raise ValueError("The identity provider did not return a subject claim.")
    return {
        "issuer": str(issuer),
        "subject": str(subject),
        "email": str(claims.get("email", "")),
        "display_name": str(claims.get("name") or claims.get("preferred_username") or claims.get("email") or ""),
    }


def show_auth_screen(oidc_enabled: bool = False) -> None:
    """Render the authentication page with a two-panel forest-and-sand design."""
    auth_config = get_auth_config()
    if auth_config["public_mode"]:
        st.info("Secure sign-in and managed PostgreSQL persistence are enabled for this deployment.")
    with st.container(key="auth_screen"):
        left, right = st.columns([1.05, .95], gap="large")
        with left:
            st.markdown("""
            <section class="auth-story">
              <div>
                <div style="font-size:2rem;margin-bottom:1.2rem;color:#FFFDF5">▰</div>
                <div class="auth-kicker" style="color:#F09A70!important">OPERATIONS RESEARCH PLATFORM</div>
                <h1>Make every supply-chain decision count.</h1>
                <p>Plan sourcing, balance warehouse flows and understand the cost of carbon with a mathematical decision-support workspace.</p>
              </div>
              <div>
                <div class="auth-feature">01 &nbsp; Optimise network flows</div>
                <div class="auth-feature">02 &nbsp; Stress-test business scenarios</div>
                <div class="auth-feature">03 &nbsp; Explore cost and emissions trade-offs</div>
                <p style="font-size:.72rem;margin-top:2rem;color:#B8CDBD!important">SUPPLYCHAIN OPTIMIZER · PRIVATE WORKSPACE ACCESS</p>
              </div>
            </section>
            """, unsafe_allow_html=True)

        with right:
            st.markdown('<div class="auth-kicker">WELCOME TO YOUR WORKSPACE</div>', unsafe_allow_html=True)
            st.subheader("Access your workspace")
            if oidc_enabled:
                st.markdown('<p class="auth-intro">Sign in with your configured identity provider. Your account and workspace access are managed securely.</p>', unsafe_allow_html=True)
                if st.button("Continue with secure sign-in", type="primary", use_container_width=True, key="oidc_login"):
                    st.login()
            elif auth_config["allow_signup"]:
                st.markdown('<p class="auth-intro">Sign in to continue, or create an account to start a private workspace.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="auth-intro">Use your approved account to access the workspace.</p>', unsafe_allow_html=True)
            options = ["Sign in"] if not oidc_enabled else []
            if auth_config["allow_signup"] and not oidc_enabled:
                options.append("Create account")
            mode = st.radio(
                "Choose an action",
                options,
                horizontal=True,
                label_visibility="collapsed",
                key="auth_mode",
            ) if options else None

            if mode == "Sign in":
                with st.form("login_form_final", clear_on_submit=False):
                    identifier = st.text_input("Username or email", key="login_identifier")
                    password = st.text_input("Password", type="password", key="login_password")
                    submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                if submitted:
                    if not identifier.strip() or not password:
                        st.error("Enter both your username/email and password.")
                    else:
                        try:
                            with st.spinner("Checking your account..."):
                                user = authenticate_user(identifier, password)
                            if user:
                                st.session_state["sc_user"] = user
                                st.session_state.pop("sc_workspace_loaded", None)
                                st.success("Sign-in successful. Opening your workspace...")
                                st.rerun()
                            else:
                                st.error("Sign-in failed. Check your username/email and password.")
                        except Exception as exc:
                            st.exception(exc)
            elif mode == "Create account":
                with st.form("register_form_final", clear_on_submit=False):
                    username = st.text_input("Username", max_chars=32, key="register_username")
                    email = st.text_input("Email address", key="register_email")
                    new_password = st.text_input("Password", type="password", help="At least 8 characters.", key="register_password")
                    confirm_password = st.text_input("Confirm password", type="password", key="register_confirm_password")
                    created = st.form_submit_button("Create account", type="primary", use_container_width=True)
                if created:
                    if not username.strip() or not email.strip() or not new_password or not confirm_password:
                        st.error("Complete all four fields before creating your account.")
                    elif new_password != confirm_password:
                        st.error("The passwords do not match.")
                    else:
                        try:
                            with st.spinner("Creating your account securely..."):
                                ok, message = register_user(username, email, new_password)
                            if ok:
                                user = authenticate_user(username, new_password)
                                if user:
                                    st.session_state["sc_user"] = user
                                    st.session_state.pop("sc_workspace_loaded", None)
                                    st.success("Account created. Opening your workspace...")
                                    st.rerun()
                                else:
                                    st.success(message)
                                    st.info("Switch to Sign in and use your new username/email and password.")
                            else:
                                st.error(message)
                        except Exception as exc:
                            st.exception(exc)

            st.divider()
            if auth_config["allow_demo_login"] and not oidc_enabled:
                if st.button("Continue with Demo Account", use_container_width=True, key="demo_login_final"):
                    try:
                        demo_user = authenticate_user("planner_demo", "demo12345")
                        if demo_user:
                            st.session_state["sc_user"] = demo_user
                            st.session_state.pop("sc_workspace_loaded", None)
                            st.rerun()
                        else:
                            st.error("Demo account could not be authenticated.")
                    except Exception as exc:
                        st.exception(exc)
            else:
                st.caption("Demo access is disabled for this deployment configuration.")
            if oidc_enabled:
                st.caption("Authentication is provided by OpenID Connect. Workspace data uses the configured persistence backend.")
            else:
                st.caption(f"Prototype authentication uses salted password hashes and {auth_config['database_backend']} storage.")


OIDC_CONFIGURED = configure_auth_from_secrets()
AUTH_CONFIG = get_auth_config()
if AUTH_CONFIG["public_mode"] and not OIDC_CONFIGURED:
    st.error("Public mode requires a complete Streamlit OpenID Connect configuration in secrets. Configure [auth] before starting the application.")
    st.stop()
if AUTH_CONFIG["public_mode"] and AUTH_CONFIG["database_backend"] != "postgresql":
    st.error("Public mode requires a managed PostgreSQL URL under SUPPLYCHAIN_DATABASE_URL or secrets [database].url. SQLite is not durable or suitable for public multi-user deployment.")
    st.stop()
init_auth_db()
if OIDC_CONFIGURED and st.user.is_logged_in:
    try:
        identity = current_oidc_identity()
        if identity:
            identity_key = f"{identity['issuer']}\0{identity['subject']}"
            if st.session_state.get("sc_identity_key") != identity_key:
                st.session_state["sc_user"] = provision_oidc_user(
                    identity["issuer"], identity["subject"], identity["email"], identity["display_name"]
                )
                st.session_state["sc_identity_key"] = identity_key
                st.session_state.pop("sc_workspace_loaded", None)
    except (ValueError, RuntimeError) as exc:
        st.error(f"Could not provision your sign-in: {exc}")
        st.stop()
elif OIDC_CONFIGURED:
    st.session_state.pop("sc_user", None)
    st.session_state.pop("sc_identity_key", None)
if "sc_user" not in st.session_state:
    show_auth_screen(oidc_enabled=OIDC_CONFIGURED)
    st.stop()


init_state()


if not st.session_state.get("sc_workspace_loaded"):
    saved = load_workspace(st.session_state["sc_user"]["id"])
    if saved:
        try:
            restored = {
                name: pd.DataFrame(saved["tables"][name])
                for name in TABLE_NAMES
            }
            if validate_tables(restored).is_valid:
                st.session_state.sc_tables = restored
            st.session_state.sc_result = saved.get("result")
            st.session_state.sc_pareto = saved.get("pareto")
            st.session_state.sc_scenario = saved.get("scenario")
        except (KeyError, TypeError, ValueError):
            st.warning("Your saved workspace could not be fully restored. The sample network remains loaded.")
    st.session_state["sc_workspace_loaded"] = True

with st.sidebar:
    st.markdown('<div style="font-size:1.55rem;margin-bottom:.45rem">▰</div><div class="brand-mark">SupplyChain<br>Optimizer</div><div class="brand-sub">NETWORK DESIGN<br>OPERATIONS RESEARCH<br>CARBON-AWARE PLANNING</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="side-kicker">WORKBENCH</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.12);padding:.65rem .75rem;border-radius:10px;margin:.8rem 0 1rem"><div style="font-size:.65rem;color:#B9CDBD">SIGNED IN AS</div><div style="font-weight:700">{html.escape(str(st.session_state["sc_user"]["username"]))}</div></div>',
        unsafe_allow_html=True
    )
    if st.button("Log out", key="logout_button", use_container_width=True):
        user_id = st.session_state["sc_user"]["id"]
        save_workspace(user_id, {
            "tables": {name: st.session_state.sc_tables[name].to_dict(orient="records") for name in TABLE_NAMES},
            "result": st.session_state.sc_result,
            "pareto": st.session_state.sc_pareto,
            "scenario": st.session_state.sc_scenario,
        })
        if OIDC_CONFIGURED:
            st.logout()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    if st.button("Reset sample network", key="reset_sample_network", use_container_width=True):
        reset_workspace_to_sample()
        st.success("Sample network restored.")
        st.rerun()
    page = st.radio(
        "Workspace",
        ["Overview", "Network & data", "Optimisation", "Scenario laboratory", "Sustainability & Pareto", "Exports & methodology"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("---")
    st.markdown('<div class="side-kicker">MODEL PROFILE</div>', unsafe_allow_html=True)
    st.caption("Single period · Single product")
    st.caption("Continuous shipment flows")
    st.caption("INR · CO₂e · Linear programming")

page_meta = {
    "Overview": ("CONTROL TOWER / 01", "Network overview", "A live view of network structure, optimisation readiness and operating performance."),
    "Network & data": ("DATA WORKSHOP / 02", "Network & data", "Configure the supply chain, inspect source tables and validate network integrity."),
    "Optimisation": ("SOLVER WORKSPACE / 03", "Optimisation", "Find the lowest-cost feasible flow plan under operational and sustainability constraints."),
    "Scenario laboratory": ("STRESS TESTING / 04", "Scenario laboratory", "Challenge the network with disruptions and changing business assumptions."),
    "Sustainability & Pareto": ("CARBON STRATEGY / 05", "Sustainability & Pareto", "Explore the cost of carbon reduction and compare efficient operating plans."),
    "Exports & methodology": ("MODEL GOVERNANCE / 06", "Exports & methodology", "Review assumptions, mathematical formulation and reproducible outputs."),
}
kicker, heading, description = page_meta[page]
ready = validate_tables(st.session_state.sc_tables).is_valid
pill = "● MODEL READY" if ready else "● DATA REVIEW NEEDED"
st.markdown(
    f'<div class="page-head"><div><div class="page-kicker">{kicker}</div><div class="page-title">{heading}</div><div class="page-desc">{description}</div></div><div class="status-pill">{pill}</div></div>',
    unsafe_allow_html=True
)

if page == "Overview":
    tables = st.session_state.sc_tables
    report = validate_tables(tables)
    st.markdown('<div class="section-eyebrow">01 / NETWORK SNAPSHOT</div>', unsafe_allow_html=True)
    st.subheader("Your operating network")
    cols = st.columns(5)
    for col, name in zip(cols, TABLE_NAMES):
        col.metric(TABLE_LABELS[name], len(tables[name]))
    st.divider()
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("How the network works")
        st.markdown('<div style="background:#E5EBDD;border:1px solid #D2DDCE;border-radius:13px;padding:1rem 1.1rem;color:#244B3B;font-weight:700;text-align:center">SUPPLIERS <span style="color:#C8794A">→</span> WAREHOUSES <span style="color:#C8794A">→</span> CUSTOMERS</div>', unsafe_allow_html=True)
        st.write("A two-stage material-flow network with explicit supplier, warehouse and customer constraints.")
        st.markdown("**Decision variables**")
        st.latex(r"x_{ik}=\text{units shipped from supplier }i\text{ to warehouse }k")
        st.latex(r"y_{kj}=\text{units shipped from warehouse }k\text{ to customer }j")
        st.markdown("**Primary objective**")
        st.latex(r"\min \; \sum_{i,k}(p_i+a_{ik})x_{ik}+\sum_{k,j}(b_{kj}+h_k)y_{kj}")
    with right:
        st.subheader("Readiness")
        if report.is_valid:
            st.success("Input data is structurally valid")
        else:
            st.error(f"{len(report.errors)} validation issue(s) detected")
            for error in report.errors[:5]:
                st.write(f"- {error}")
        if st.session_state.sc_result:
            st.info(f"Last optimisation: {st.session_state.sc_result.get('status')}")
        else:
            st.info("No optimisation has been run in this session yet.")
        if st.session_state.sc_pareto:
            st.info(f"Pareto analysis: {st.session_state.sc_pareto.get('frontier_point_count', 0)} frontier points")
    st.divider()
    st.markdown('<div class="section-eyebrow">02 / DECISION CYCLE</div>', unsafe_allow_html=True)
    st.subheader("From raw network data to an operating plan")
    flow = st.columns(5)
    steps = [("01", "Configure", "Entities & routes"), ("02", "Validate", "Check constraints"), ("03", "Optimise", "Solve the LP"), ("04", "Stress-test", "Compare scenarios"), ("05", "Decide", "Review trade-offs")]
    for col, (number, title, sub) in zip(flow, steps):
        col.markdown(f'<div style="background:#FBFAF6;border:1px solid #E2E5DC;border-radius:12px;padding:.8rem;min-height:112px"><div style="color:#C8794A;font-size:.68rem;font-weight:800;letter-spacing:.12em">{number}</div><div style="color:#183D32;font-weight:800;margin:.35rem 0">{title}</div><div style="color:#718078;font-size:.75rem">{sub}</div></div>', unsafe_allow_html=True)

elif page == "Network & data":
    st.subheader("Network data management")
    st.markdown('<p class="section-note">Upload CSV files using the canonical table names and required columns, or edit the sample network directly.</p>', unsafe_allow_html=True)
    with st.expander("Upload data tables", expanded=True):
        uploaded: dict[str, pd.DataFrame] = {}
        upload_cols = st.columns(2)
        for idx, name in enumerate(TABLE_NAMES):
            file = upload_cols[idx % 2].file_uploader(f"{TABLE_LABELS[name]} CSV", type=["csv"], key=f"upload_{name}")
            if file is not None:
                try:
                    uploaded[name] = pd.read_csv(file)
                except Exception as exc:
                    st.error(f"Could not read {file.name}: {exc}")
        if st.button("Apply uploaded tables", type="primary", disabled=len(uploaded) != 5):
            st.session_state.sc_tables = uploaded
            st.session_state.sc_result = None
            st.session_state.sc_pareto = None
            st.session_state.sc_scenario = None
            st.success("All five uploaded tables have been loaded. Validate them below.")
        if uploaded and len(uploaded) != 5:
            st.caption(f"{len(uploaded)} of 5 tables uploaded. Upload all five before applying a replacement dataset.")
        if st.button("Reset to sample data", type="secondary"):
            reset_workspace_to_sample()
            st.success("Sample tables restored.")
    with st.expander("Download blank CSV templates"):
        for name in TABLE_NAMES:
            template_path = ROOT / "data" / "templates" / f"{name}.csv"
            if template_path.exists():
                st.download_button(f"Download {TABLE_LABELS[name]} template", template_path.read_bytes(), file_name=f"{name}.csv", mime="text/csv", key=f"template_{name}")
    st.divider()
    st.subheader("Edit current data")
    for name in TABLE_NAMES:
        with st.expander(TABLE_LABELS[name], expanded=False):
            edited = st.data_editor(st.session_state.sc_tables[name], num_rows="dynamic", use_container_width=True, key=f"editor_{name}")
            st.session_state.sc_tables[name] = edited
            st.download_button(f"Download {name}.csv", edited.to_csv(index=False).encode("utf-8"), file_name=f"{name}.csv", mime="text/csv", key=f"download_{name}")
    st.divider()
    if st.button("Validate current network", type="primary"):
        show_validation(st.session_state.sc_tables)

elif page == "Optimisation":
    st.subheader("Optimisation workspace")
    st.markdown("Minimise total procurement, transport and handling cost while satisfying supply, flow-balance, warehouse, route, demand and delivery-window constraints.")
    carbon_enabled = st.checkbox("Apply a maximum carbon-emissions limit", value=False)
    carbon_cap = None
    if carbon_enabled:
        carbon_cap = st.number_input("Maximum emissions (kg CO₂e)", min_value=0.0, value=1280.0, step=10.0)
    if st.button("Run optimisation", type="primary"):
        if show_validation(st.session_state.sc_tables):
            with st.spinner("Solving the linear programming model…"):
                st.session_state.sc_result = solve_network(st.session_state.sc_tables, emissions_cap_kg=carbon_cap)
    result = st.session_state.sc_result
    if result:
        st.divider()
        st.subheader("Solver result")
        result_kpis(result)
        if result.get("status") == "Optimal":
            st.caption(f"Solver status: {result['status']} · {result['model_statistics']['decision_variable_count']} decision variables · {result['model_statistics']['constraint_count']} constraints")
            tab1, tab2, tab3, tab4 = st.tabs(["Allocations", "Cost breakdown", "Capacity utilisation", "Route metrics"])
            with tab1:
                allocation = allocations_frame(result)
                st.dataframe(allocation, use_container_width=True, hide_index=True)
                if not allocation.empty:
                    st.download_button("Download allocation CSV", allocation.to_csv(index=False).encode(), "optimised_allocations.csv", "text/csv")
            with tab2:
                cost_df = pd.DataFrame([{"Cost component": k.replace("_inr", "").replace("_", " ").title(), "INR": v} for k, v in result["cost_breakdown"].items()])
                st.bar_chart(cost_df.set_index("Cost component"))
                st.dataframe(cost_df, use_container_width=True, hide_index=True)
            with tab3:
                util = pd.DataFrame(result["warehouse_utilisation"])
                st.bar_chart(util.set_index("warehouse_id")["utilisation_pct"])
                st.dataframe(util, use_container_width=True, hide_index=True)
            with tab4:
                routes = pd.DataFrame(result["route_metrics"])
                st.dataframe(routes, use_container_width=True, hide_index=True)
            st.download_button("Download complete optimisation result (JSON)", json.dumps(result, indent=2), "optimisation_result.json", "application/json")

elif page == "Scenario laboratory":
    st.subheader("Scenario laboratory")
    st.markdown("Change one assumption at a time, re-optimise the network and compare the result with the current baseline.")
    baseline = solve_network(st.session_state.sc_tables)
    if baseline.get("status") != "Optimal":
        st.error("The current baseline network must be feasible before scenario analysis.")
        result_kpis(baseline)
    else:
        scenario_type = st.selectbox("Scenario type", ["Supplier purchase-price shock", "Supplier disruption", "Demand growth", "Warehouse capacity reduction", "Carbon emissions cap"])
        suppliers = st.session_state.sc_tables["suppliers"]["supplier_id"].astype(str).tolist()
        warehouses = st.session_state.sc_tables["warehouses"]["warehouse_id"].astype(str).tolist()
        scenario: dict[str, Any] = {"name": scenario_type}
        if scenario_type == "Supplier purchase-price shock":
            supplier = st.selectbox("Supplier", suppliers)
            pct = st.slider("Purchase-price increase (%)", 0, 200, 10, 5)
            scenario.update(type="supplier_price_shock", supplier_id=supplier, increase_pct=pct)
        elif scenario_type == "Supplier disruption":
            supplier = st.selectbox("Supplier", suppliers)
            scenario.update(type="supplier_disruption", supplier_id=supplier)
        elif scenario_type == "Demand growth":
            pct = st.slider("Demand change (%)", -50, 200, 20, 5)
            scenario.update(type="demand_growth", increase_pct=pct)
        elif scenario_type == "Warehouse capacity reduction":
            warehouse = st.selectbox("Warehouse", warehouses)
            pct = st.slider("Capacity reduction (%)", 0, 100, 25, 5)
            scenario.update(type="warehouse_capacity_reduction", warehouse_id=warehouse, reduction_pct=pct)
        else:
            cap = st.number_input("Maximum emissions (kg CO₂e)", min_value=0.0, value=1200.0, step=10.0)
            scenario.update(type="carbon_cap", emissions_cap_kg=cap)
        if st.button("Run scenario", type="primary"):
            try:
                if scenario["type"] == "carbon_cap":
                    changed = {k: v.copy(deep=True) for k, v in st.session_state.sc_tables.items()}
                    result = solve_network(changed, emissions_cap_kg=scenario["emissions_cap_kg"], scenario_mode=True)
                    from supplychain.scenario_analysis import compare_results
                    output = {"scenario": scenario, "result": result, "comparison": compare_results(baseline, result)}
                else:
                    output = run_scenario(st.session_state.sc_tables, scenario, baseline)
                st.session_state.sc_scenario = output
            except Exception as exc:
                st.error(f"Scenario could not be run: {exc}")
        output = st.session_state.sc_scenario
        if output:
            st.divider()
            st.subheader(output["scenario"].get("name", "Scenario result"))
            result_kpis(output["result"])
            comp = output["comparison"]
            a, b, c = st.columns(3)
            a.metric("Cost change", money(comp.get("cost_change_inr")), None if comp.get("cost_change_inr") is None else f"{comp.get('cost_change_pct', 0):+.2f}%")
            b.metric("Emissions change", "—" if comp.get("emissions_change_kg_co2e") is None else f"{comp['emissions_change_kg_co2e']:+,.1f} kg")
            b2 = comp.get("delivery_change_hours")
            c.metric("Delivery-time change", "—" if b2 is None else f"{b2:+,.2f} h")
            changes = pd.DataFrame(comp.get("route_allocation_changes", []))
            if not changes.empty:
                st.markdown("**Changed route allocations**")
                st.dataframe(changes, use_container_width=True, hide_index=True)
            st.download_button("Download scenario result (JSON)", json.dumps(output, indent=2), "scenario_result.json", "application/json")

elif page == "Sustainability & Pareto":
    st.subheader("Sustainability and multi-objective analysis")
    st.markdown("The epsilon-constraint method minimises operating cost while progressively tightening the maximum allowable CO₂e emissions.")
    points = st.slider("Number of emissions-cap points", min_value=2, max_value=51, value=11, step=1)
    if st.button("Calculate Pareto frontier", type="primary"):
        if show_validation(st.session_state.sc_tables):
            with st.spinner(f"Solving {points + 2} linear programmes (including endpoint calculations)…"):
                st.session_state.sc_pareto = run_pareto_analysis(st.session_state.sc_tables, points=points)
    report = st.session_state.sc_pareto
    if report:
        if report.get("status") != "Completed":
            st.error(report.get("diagnostic", report.get("status", "Analysis failed")))
        else:
            a, b, c, d = st.columns(4)
            a.metric("Minimum emissions", f"{report['minimum_emissions_kg_co2e']:,.1f} kg")
            b.metric("Cost at minimum emissions", money(report["minimum_emissions_solution_cost_inr"]))
            c.metric("Minimum operating cost", money(report["minimum_cost_inr"]))
            d.metric("Frontier points", report["frontier_point_count"])
            frontier = pd.DataFrame(report["pareto_frontier"])
            st.subheader("Cost–emissions frontier")
            fig = px.scatter(frontier, x="emissions_kg_co2e", y="cost_inr", hover_data=["emissions_cap_kg_co2e", "average_delivery_hours"], labels={"emissions_kg_co2e": "Total emissions (kg CO₂e)", "cost_inr": "Operating cost (INR)"}, title="Pareto-efficient supply-chain plans")
            fig.update_traces(mode="lines+markers", line=dict(color="#C8794A", width=3), marker=dict(color="#245545", size=9))
            fig.update_layout(height=470, paper_bgcolor="#FBFAF6", plot_bgcolor="#FBFAF6",
                font=dict(family="DM Sans, sans-serif", color="#26352E"),
                title_font=dict(family="Manrope, sans-serif", color="#183D32"),
                xaxis=dict(gridcolor="#E7E9E1", zerolinecolor="#D7DDD3"),
                yaxis=dict(gridcolor="#E7E9E1", zerolinecolor="#D7DDD3"),
                margin=dict(l=25, r=20, t=55, b=25))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(frontier[["emissions_cap_kg_co2e", "cost_inr", "emissions_kg_co2e", "average_delivery_hours"]], use_container_width=True, hide_index=True)
            sweep = pd.DataFrame(report["sweep"])
            st.download_button("Download Pareto frontier CSV", frontier.to_csv(index=False).encode(), "pareto_frontier.csv", "text/csv")
            st.download_button("Download full epsilon sweep CSV", sweep.to_csv(index=False).encode(), "pareto_sweep.csv", "text/csv")
            st.download_button("Download Pareto report JSON", json.dumps(report, indent=2), "pareto_analysis.json", "application/json")

elif page == "Exports & methodology":
    st.subheader("Exports and reproducibility")
    st.markdown("All optimisation results in this application are generated from the current network tables. The benchmark dataset is synthetic and intended for demonstration, not as a claim about a real company.")
    st.markdown("**Model assumptions**")
    st.markdown("- Deterministic, single-period, single-product network.\n- Continuous, non-negative shipment quantities.\n- Fixed unit procurement, transport and handling costs.\n- Fixed route capacities, lead times and emissions factors.\n- Warehouse flow conservation: total inbound flow equals total outbound flow.\n- Customer demand is met exactly.\n- Outbound routes exceeding a customer's maximum delivery time are disabled.")
    st.markdown("**Not currently modelled**")
    st.markdown("- Multi-period inventory and replenishment.\n- Stochastic demand or uncertain lead times.\n- Integer vehicle, pallet or package decisions.\n- Vehicle routing and fixed-charge facility activation.\n- Multi-product substitution or shared capacities.")
    st.markdown("**Mathematical formulation**")
    st.latex(r"\min \sum_{(i,k)}(p_i+a_{ik})x_{ik}+\sum_{(k,j)}(b_{kj}+h_k)y_{kj}")
    st.latex(r"\sum_k x_{ik}\leq s_i,\quad \sum_i x_{ik}=\sum_j y_{kj},\quad \sum_i x_{ik}\leq C_k")
    st.latex(r"\sum_k y_{kj}=d_j,\quad 0\leq x_{ik}\leq U_{ik},\quad 0\leq y_{kj}\leq V_{kj}")
    st.latex(r"\sum_{(i,k)}e_{ik}x_{ik}+\sum_{(k,j)}f_{kj}y_{kj}\leq E_{\max}")
    st.markdown("**Reproducibility files**")
    if st.session_state.sc_result:
        st.download_button("Download last optimisation result", json.dumps(st.session_state.sc_result, indent=2), "optimisation_result.json", "application/json")
    if st.session_state.sc_pareto:
        st.download_button("Download last Pareto report", json.dumps(st.session_state.sc_pareto, indent=2), "pareto_analysis.json", "application/json")
    st.caption("Solver: PuLP with CBC. Interface: Streamlit. Charts: Plotly. Input/output tables: pandas.")

st.divider()
st.markdown('<div style="border-top:1px solid #E2E5DC;padding-top:.8rem;color:#87938B;font-size:.72rem;letter-spacing:.04em">SUPPLYCHAIN OPTIMIZER · RESEARCH PROTOTYPE · VERIFY INPUT ASSUMPTIONS BEFORE OPERATIONAL USE</div>', unsafe_allow_html=True)


# Persist the active user's workspace after each completed interaction/rerun.
if "sc_user" in st.session_state and all(key in st.session_state for key in ["sc_tables", "sc_result", "sc_pareto", "sc_scenario"]):
    save_workspace(
        st.session_state["sc_user"]["id"],
        {
            "tables": {name: st.session_state.sc_tables[name].to_dict(orient="records") for name in TABLE_NAMES},
            "result": st.session_state.sc_result,
            "pareto": st.session_state.sc_pareto,
            "scenario": st.session_state.sc_scenario,
        },
    )
