# streamlit_app.py
"""
Streamlit-native replacement UI for World Bank — IATI Intelligence Agent.

Features:
- Loads prompt_templates.json (expert_prompts + quick_actions)
- Masks environment secrets on the sidebar (do NOT show raw secrets)
- Cached orchestrator initialization with graceful error handling
- Chat, Dashboard Builder, Analytics, Docs tabs
- Uses st.session_state for query text population and quick actions
"""

from __future__ import annotations
import streamlit as st
import asyncio
import json
import os
import io
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

import plotly.express as px
import pandas as pd

def render_dashboard(dash: dict):
    """
    Renders a DashboardLayout-like dict (from dashboard_framework exporter / orchestrator response)
    into Streamlit KPIs + charts. Falls back gracefully if real data isn't available yet.
    """

    st.markdown(f"## {dash.get('title','Executive Dashboard')}")
    if dash.get("description"):
        st.caption(dash["description"])

    comps = dash.get("components", [])
    if not isinstance(comps, list) or not comps:
        st.info("No dashboard components found.")
        return

    # --- 1) KPI Row (kpi_card) ---
    kpis = [c for c in comps if c.get("type") in ("kpi_card", "kpi", "metric")]
    if kpis:
        cols = st.columns(min(4, len(kpis)))
        for i, c in enumerate(kpis[:4]):
            cfg = c.get("configuration", {}) or {}
            # placeholder values (until you wire live data sources)
            metric_name = cfg.get("metric", c.get("title","Metric"))
            value = cfg.get("target", None)
            if value is None:
                # nice-looking defaults
                value = 75 if "ratio" in metric_name or "efficiency" in metric_name else 500
            delta = None
            cols[i].metric(c.get("title","KPI"), value, delta)

    st.divider()

    # --- 2) Charts (bar/line/pie/heatmap/etc.) ---
    charts = [c for c in comps if c.get("type") not in ("kpi_card", "kpi", "metric")]
    for c in charts:
        ctype = c.get("type")
        title = c.get("title", ctype)
        cfg = c.get("configuration", {}) or {}

        st.subheader(title)

        # For now, create tasteful placeholder datasets if no real data binding exists.
        # Later: replace this with real data lookups based on c["data_source"] and cfg fields.
        if ctype in ("bar", "bar_chart", "sector_bar"):
            df = pd.DataFrame({
                "Category": ["Africa", "Asia", "Education", "Health", "Europe", "MENA"],
                "Value": [28, 18, 24, 19, 6, 3]
            })
            fig = px.bar(df, x="Category", y="Value")
            st.plotly_chart(fig, use_container_width=True)

        elif ctype in ("line", "line_chart", "trend"):
            df = pd.DataFrame({
                "Year": [2019, 2020, 2021, 2022, 2023, 2024],
                "Investment": [210, 235, 250, 300, 270, 310],
                "Disbursement": [95, 110, 135, 160, 190, 230]
            })
            fig = px.line(df, x="Year", y=["Investment", "Disbursement"])
            st.plotly_chart(fig, use_container_width=True)

        elif ctype in ("pie", "pie_chart"):
            df = pd.DataFrame({
                "Sector": ["Health", "Education", "Infrastructure", "Energy"],
                "Share": [26, 22, 32, 20]
            })
            fig = px.pie(df, names="Sector", values="Share")
            st.plotly_chart(fig, use_container_width=True)

        elif ctype in ("heatmap", "risk_heatmap"):
            df = pd.DataFrame([
                ["High", 7, 4, 8, 12, 30, 36, 25],
                ["Moderate", 8, 15, 12, 12, 12, 23, 25],
                ["Low", 8, 5, 6, 15, 17, 25, 26],
                ["Stable", 7, 3, 5, 15, 25, 23, 25],
            ], columns=["Band","Geo","Econ","Fin","Social","Env","Ops","Cyber"])
            fig = px.imshow(df.set_index("Band"), aspect="auto")
            st.plotly_chart(fig, use_container_width=True)

        else:
            # Unknown type: show config so it’s still useful
            st.caption("Component configuration")
            st.json({"type": ctype, "data_source": c.get("data_source"), "configuration": cfg})


# Project imports - ensure these modules exist in your repo
from wb_iati_agent_config import get_agent_config
from main_agent_orchestrator import WBIATIAgentOrchestrator
# safe_async.py snippet — paste into streamlit_app.py near the top (after imports)
import asyncio

def run_async_safely(coro):
    """
    Run an async coroutine safely from sync code in environments where an
    event loop might already be running (like Streamlit).
    Usage: run_async_safely(orchestrator.some_async_method(...))
    """
    try:
        # Typical case when no loop is running
        return asyncio.run(coro)
    except RuntimeError as e:
        # event loop already running -> use nest_asyncio to allow nested run
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)


# ---- Page config and lightweight styling ----
st.set_page_config(page_title="WB IATI Intelligence Agent", layout="wide", initial_sidebar_state="expanded")

_GRADIENT_CSS = """
<style>
:root{ --bg:#f7fbfc; --card-bg:#ffffff; --muted:#6b7280; }
html,body [data-testid="stAppViewContainer"]{ background: var(--bg); }
.header { background: linear-gradient(90deg, #0ea5a9 0%, #38bdf8 45%, #60a5fa 100%); padding: 24px 28px; border-radius: 10px; color: white; box-shadow: 0 6px 20px rgba(13,36,62,0.08); }
.header h1{ margin:0; font-weight:700; font-size:26px; }
.card{ background: var(--card-bg); border-radius:10px; padding:14px; box-shadow: 0 6px 18px rgba(12,38,70,0.04); }
.small-muted{ color:var(--muted); font-size:0.95rem; }
.example-box{ background: linear-gradient(180deg, rgba(239,246,255,0.6), rgba(255,255,255,0.8)); border-radius:8px; padding:10px; font-family:monospace; font-size:0.95rem; }
.footer{ color:#6b7280; font-size:0.9rem; padding-top:8px; }
</style>
"""
st.markdown(_GRADIENT_CSS, unsafe_allow_html=True)

# ---- Prompt templates file path ----
PROMPT_FILE = Path("prompt_templates.json")

def load_prompt_templates() -> Dict[str, Dict[str, str]]:
    """Load prompt templates (expert_prompts and quick_actions) from JSON file."""
    try:
        if PROMPT_FILE.exists():
            with open(PROMPT_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                # Ensure keys exist
                return {
                    "expert_prompts": data.get("expert_prompts", {}),
                    "quick_actions": data.get("quick_actions", {})
                }
    except Exception as e:
        st.warning(f"Could not load prompt templates: {e}")
    return {"expert_prompts": {}, "quick_actions": {}}

# ---- Helper: masked environment display ----
def mask_value(v: Optional[str], keep_end: int = 6) -> Optional[str]:
    if not v:
        return None
    if len(v) <= keep_end + 4:
        return "****"
    return "****" + v[-keep_end:]

# ---- Cached orchestrator initialization ----
@st.cache_resource(ttl=60*60)
def get_orchestrator():
    """
    Create and initialize the WBIATIAgentOrchestrator.
    This is cached to avoid re-initializing on each rerun.
    """
    cfg = get_agent_config()
    # prefer environment variables (Streamlit secrets) if present
    cfg.api_key = os.environ.get("DO_API_KEY", getattr(cfg, "api_key", None))
    cfg.endpoint = os.environ.get("DO_ENDPOINT", getattr(cfg, "endpoint", None))
    cfg.chatbot_id = os.environ.get("DO_CHATBOT_ID", getattr(cfg, "chatbot_id", None))

    orchestrator = WBIATIAgentOrchestrator(cfg)
    try:
        # safe short initialization. Orchestrator.initialize() is expected to be async.
        init_ok = False
        try:
            init_ok = asyncio.run(orchestrator.initialize())
        except RuntimeError:
            # In some Streamlit runtimes event loop may already be running; fallback to nest_asyncio-run pattern
            # but prefer to catch errors gracefully and mark not-initialized.
            init_ok = False

        orchestrator.is_initialized = bool(init_ok)
        orchestrator.init_error = None if init_ok else getattr(orchestrator, "init_error", None)
    except Exception as e:
        orchestrator.is_initialized = False
        orchestrator.init_error = str(e)
    return orchestrator

# instantiate orchestrator (cached)
orchestrator = get_orchestrator()

# ---- Header / Hero ----
st.markdown(
    f"""
    <div class="header">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <h1>World Bank — IATI Intelligence Agent</h1>
          <p class="small-muted">Natural-language access to portfolio insights, executive dashboards, and analytics.</p>
        </div>
        <div style="text-align:right">
          <div class="small-muted" style="margin-top:6px">Deployed: <strong>{datetime.utcnow().strftime('%Y-%m-%d')}</strong></div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")  # spacer

# ---- Layout: left main column (chat / builder / analytics) and right sidebar pane ----
left_col, right_col = st.columns([3, 1])

with left_col:
    tabs = st.tabs(["Chat", "Dashboard Builder", "Analytics", "Documentation"])

    # ---------- CHAT TAB ----------
    with tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Ask the agent")
        st.markdown("<div class='small-muted'>Type a natural-language question about projects, finance, locations, or request an executive summary.</div>", unsafe_allow_html=True)

        # Load prompts and quick actions
        PROMPTS = load_prompt_templates()
        EXPERT_PROMPTS = PROMPTS.get("expert_prompts", {}) or {}
        QUICK_ACTIONS = PROMPTS.get("quick_actions", {}) or {}

        # initialize session_state for query text
        if "query_text" not in st.session_state:
            st.session_state["query_text"] = ""

        # Expert prompt selector
        if EXPERT_PROMPTS:
            st.markdown("**Expert templates**")
            # show user-friendly names in selectbox, keep mapping
            keys = [""] + list(EXPERT_PROMPTS.keys())
            chosen = st.selectbox("Choose a template", options=keys, format_func=lambda k: (k if k else "— select a template —"))
            if chosen:
                st.markdown(f"**Template preview:** {EXPERT_PROMPTS[chosen]}")
                if st.button("Use this template"):
                    st.session_state["query_text"] = EXPERT_PROMPTS[chosen]

        # Quick actions as compact buttons
        if QUICK_ACTIONS:
            st.markdown("**Quick actions**")
            qa_items = list(QUICK_ACTIONS.items())
            # create up to 3 columns for quick-action buttons
            cols = st.columns(min(3, max(1, len(qa_items))))
            for i, (k, v) in enumerate(qa_items):
                if cols[i % len(cols)].button(k.replace("_", " ").title()):
                    st.session_state["query_text"] = v

        # Query area
        query = st.text_area("Enter your natural language query", height=160, value=st.session_state["query_text"], key="query_input")
        auto_dashboard = st.toggle("Auto-generate portfolio dashboard after query", value=True)

        # Buttons
        col_run, col_dash, col_clear = st.columns([1,1,1])
        run_btn = col_run.button("Run Query")
        dashboard_btn = col_dash.button("Create Executive Dashboard")
        clear_btn = col_clear.button("Clear")

        if clear_btn:
            st.session_state["query_text"] = ""
            st.session_state["query_input"] = ""
            st.experimental_rerun()

        # Helper to normalize responses (dict-like or dataclass-like)
        def _resp_to_dict(resp: Any) -> Dict[str, Any]:
            if resp is None:
                return {}
            # if it's an APIResponse dataclass with .to_dict()
            if hasattr(resp, "to_dict"):
                try:
                    return resp.to_dict()
                except Exception:
                    pass
            # if it is mapping-like
            if isinstance(resp, dict):
                return resp
            # if has attributes
            if hasattr(resp, "__dict__"):
                return vars(resp)
            # fallback: string or other
            return {"raw": resp}

        # Run query
        if run_btn:
            if not query or not query.strip():
                st.warning("Please enter a query before running.")
            else:
                with st.spinner("Processing query..."):
                    try:
                        # some orchestrator methods are async; safe-call with asyncio.run()
                        result = {}
                        try:
                            result = asyncio.run(orchestrator.process_user_query(query))
                        except RuntimeError:
                            # event loop already running (rare on Streamlit) — attempt direct call if available sync
                            # fallback: attempt if orchestrator exposes a sync wrapper process_user_query_sync
                            if hasattr(orchestrator, "process_user_query_sync"):
                                result = orchestrator.process_user_query_sync(query)
                            else:
                                raise
                        result_dict = _resp_to_dict(result)
                        if result_dict.get("error") or result_dict.get("success") is False:
                            st.error(result_dict.get("error") or result_dict)
                        else:
                            st.success("Query processed")
                            exec_sum = result_dict.get("executive_summary") or result_dict.get("summary") or result_dict.get("data") or ""
                            if exec_sum:
                                st.markdown("**Executive summary**")
                                st.info(exec_sum)
                            insights = result_dict.get("key_insights") or result_dict.get("insights") or []
                            if isinstance(insights, (list, tuple)) and insights:
                                st.markdown("**Key insights**")
                                for it in insights[:12]:
                                    # try to extract title/finding gracefully
                                    if isinstance(it, dict):
                                        title = it.get("title") or it.get("label") or ""
                                        finding = it.get("finding") or it.get("text") or it.get("content") or ""
                                    else:
                                        title = ""
                                        finding = str(it)
                                    if title:
                                        st.markdown(f"- **{title}** — {finding}")
                                    else:
                                        st.markdown(f"- {finding}")
                            # raw JSON dump
                            with st.expander("Raw response (JSON)"):
                                st.json(result_dict)
                    except Exception as e:
                        st.error(f"Query processing failed: {e}")

        # Create dashboard from current text/context
        if dashboard_btn:
            with st.spinner("Creating executive dashboard..."):
                try:
                    payload_text = query.strip() or st.session_state.get("query_text", "")
                    # if payload_text is JSON-like try to parse
                    ctx = {}
                    try:
                        if payload_text.startswith("{"):
                            ctx = json.loads(payload_text)
                        else:
                            ctx = {"description": payload_text}
                    except Exception:
                        ctx = {"description": payload_text}

                    result = {}
                    try:
                        result = asyncio.run(orchestrator.create_executive_dashboard("executive", title="Executive Dashboard", context=ctx))
                    except RuntimeError:
                        if hasattr(orchestrator, "create_executive_dashboard_sync"):
                            result = orchestrator.create_executive_dashboard_sync("executive", title="Executive Dashboard", context=ctx)
                        else:
                            raise
                    result_dict = _resp_to_dict(result)
                    if result_dict.get("error"):
                        st.error(result_dict.get("error"))
                    else:
                        st.success("Dashboard created")
                        # prefer a JSON config field if present
                        config_json = result_dict.get("config_json") or result_dict.get("configurations", {}).get("json") or json.dumps(result_dict, default=str, indent=2)
                        st.download_button("Download dashboard JSON", config_json, file_name="executive_dashboard.json", mime="application/json")
                        st.markdown("**Components**")
                        comps = result_dict.get("components") or result_dict.get("widgets") or []
                        try:
                            if isinstance(comps, str):
                                comps = json.loads(comps)
                        except Exception:
                            pass
                        if comps:
                            for c in comps[:12]:
                                if isinstance(c, dict):
                                    st.markdown(f"- **{c.get('title','widget')}** — {c.get('type','')}")
                                else:
                                    st.markdown(f"- {str(c)}")
                except Exception as e:
                    st.error(f"Dashboard creation failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- DASHBOARD BUILDER TAB ----------
    with tabs[1]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Executive Dashboard Builder")
        st.markdown("<div class='small-muted'>Create an executive dashboard JSON from a short brief or query context.</div>", unsafe_allow_html=True)

        dash_title = st.text_input("Dashboard title", value="Executive Portfolio Summary")
        dash_scope = st.selectbox("Scope", options=["global", "country", "sector", "project"], index=0)
        dash_context = st.text_area("Context (optional free text or JSON)", height=120, placeholder='E.g. {"country":"Ethiopia","year":2025} or "focus on energy sector"')
        create_btn = st.button("Create dashboard from template")

        if create_btn:
            with st.spinner("Creating dashboard..."):
                try:
                    ctx = {}
                    try:
                        if dash_context.strip().startswith("{"):
                            ctx = json.loads(dash_context)
                        else:
                            ctx = {"description": dash_context}
                    except Exception:
                        ctx = {"description": dash_context}

                    result = {}
                    try:
                        result = asyncio.run(orchestrator.create_executive_dashboard(dash_scope, title=dash_title, context=ctx))
                    except RuntimeError:
                        if hasattr(orchestrator, "create_executive_dashboard_sync"):
                            result = orchestrator.create_executive_dashboard_sync(dash_scope, title=dash_title, context=ctx)
                        else:
                            raise
                    result_dict = _resp_to_dict(result)
                    if result_dict.get("error"):
                        st.error(result_dict.get("error"))
                    else:
                        st.success("Dashboard created")
                        config_json = result_dict.get("config_json") or result_dict.get("configurations", {}).get("json") or json.dumps(result_dict, default=str, indent=2)
                        st.download_button("Download dashboard JSON", config_json, file_name=f"{dash_title.replace(' ','_')}.json", mime="application/json")
                        st.write("Preview components")
                        comps = result_dict.get("components") or []
                        for c in (comps or [])[:12]:
                            st.markdown(f"- {c.get('title','widget') if isinstance(c, dict) else str(c)}")
                except Exception as e:
                    st.error(f"Creation failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- ANALYTICS TAB ----------
    with tabs[2]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Analytics workspace")
        st.markdown("<div class='small-muted'>Run quick analytics on IATI datasets or export a sample CSV for downstream analysis.</div>", unsafe_allow_html=True)

        analytics_action = st.selectbox("Action", options=["Top countries by active project count", "Export sample CSV", "Run custom analytic (NL)"])
        run_analytics_btn = st.button("Run analytics")

        if run_analytics_btn:
            with st.spinner("Running analytics..."):
                try:
                    if analytics_action == "Export sample CSV":
                        csv_buf = io.StringIO()
                        csv_buf.write("country,active_projects,total_disbursed_usd\n")
                        csv_buf.write("Ethiopia,42,120000000\n")
                        csv_buf.write("Kenya,35,98000000\n")
                        csv_buf.write("Nigeria,28,87000000\n")
                        csv_bytes = csv_buf.getvalue().encode("utf-8")
                        st.download_button("Download sample analytics CSV", csv_bytes, file_name="sample_analytics.csv", mime="text/csv")
                    else:
                        if hasattr(orchestrator, "run_analytics"):
                            analytic_result = {}
                            try:
                                analytic_result = asyncio.run(orchestrator.run_analytics(analytics_action))
                            except RuntimeError:
                                if hasattr(orchestrator, "run_analytics_sync"):
                                    analytic_result = orchestrator.run_analytics_sync(analytics_action)
                                else:
                                    raise
                            st.write(analytic_result)
                        else:
                            st.info("Analytics function not available. Showing sample output.")
                            st.table([{"country":"Ethiopia","active_projects":42},{"country":"Kenya","active_projects":35}])
                except Exception as e:
                    st.error(f"Analytics failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- DOCUMENTATION TAB ----------
    with tabs[3]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Docs & Quickstart")
        st.markdown("""
        - **How to use**: Enter a question in *Chat* or build a targeted executive dashboard via *Dashboard Builder*.
        - **Secrets**: Set `DO_API_KEY`, `DO_ENDPOINT`, `DO_CHATBOT_ID` in Streamlit Cloud secrets or environment variables.
        - **Run locally**: `pip install -r requirements.txt` then `streamlit run streamlit_app.py`.
        """)
        st.markdown("**Notes**")
        st.markdown("- Treat model outputs as advisory; sanitize before operational use.")
        st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Agent status")

    # show masked environment info
    endpoint = os.environ.get("DO_ENDPOINT")
    chatbot = os.environ.get("DO_CHATBOT_ID")
    api_present = bool(os.environ.get("DO_API_KEY"))

    st.markdown(f"- **Agent endpoint:** {mask_value(endpoint) or 'Not configured'}")
    st.markdown(f"- **Chatbot ID:** {mask_value(chatbot) or 'Not configured'}")
    st.markdown(f"- **API key present:** {'✅' if api_present else '❌'}")

    st.markdown("---")
    # orchestrator status (cached)
    status_info = {
        "name": getattr(orchestrator, "name", "World Bank IATI Intelligence Agent"),
        "version": getattr(orchestrator, "version", "1.0.0"),
        "initialized": getattr(orchestrator, "is_initialized", False),
        "endpoint": mask_value(getattr(orchestrator, "config", {}).endpoint if hasattr(orchestrator, "config") else endpoint)
    }

    st.write(status_info)
    if not status_info["initialized"]:
        st.warning("Agent not fully initialized. Check logs and secrets.")
        init_err = getattr(orchestrator, "init_error", None) or getattr(orchestrator, "_init_error", None)
        if init_err:
            st.markdown(f"**Init error:** {init_err}")

    st.markdown("---")
    st.subheader("Example prompts")
    st.markdown("<div class='example-box'>", unsafe_allow_html=True)
    st.markdown("1. Summarize active projects in **Kenya** by sector and last disbursement date.")
    st.markdown("2. Create an executive dashboard focused on energy projects in **Ethiopia**.")
    st.markdown("3. List projects with > $50M disbursed in the last 3 years.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Run Demo Query"):
        # populate demo query into the session and rerun so user sees it in the input
        st.session_state["query_text"] = "Summarize active projects in Kenya by sector and risk level."
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---- Footer ----
st.markdown("<div class='footer'>Built with care — treat model outputs as advisory. Sanitize before operational use.</div>", unsafe_allow_html=True)
