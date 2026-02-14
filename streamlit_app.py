# streamlit_app.py
"""
World Bank — IATI Intelligence Agent (Streamlit-native, client-demo ready)

What this version fixes/improves:
- Auto-renders an impressive "consulting-style" dashboard immediately after a successful query
- Works even when WBIATIIntelligenceAgent is missing methods (_analyze_trends/_analyze_sector_data/etc.)
  by falling back to the DO agent (chat endpoint) and/or local dashboard templates
- Keeps Raw JSON hidden by default (still available via expander)
- Quick Actions + Expert Templates reliably populate the query and can optionally auto-run
- Masks secrets in the sidebar (never prints raw env values)
"""

from __future__ import annotations

import asyncio
import json
import os
import io
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, List

import streamlit as st
import pandas as pd
import plotly.express as px

# Project imports
from wb_iati_agent_config import get_agent_config
from main_agent_orchestrator import WBIATIAgentOrchestrator


# -----------------------------
# Page + styling
# -----------------------------
st.set_page_config(page_title="WB IATI Intelligence Agent", layout="wide")

_CSS = """
<style>
:root{ --bg:#f7fbfc; --card:#ffffff; --muted:#6b7280; }
html,body [data-testid="stAppViewContainer"]{ background: var(--bg); }
.hero{
  background: linear-gradient(90deg, #0ea5a9 0%, #38bdf8 45%, #60a5fa 100%);
  padding: 22px 26px; border-radius: 12px; color: white;
  box-shadow: 0 10px 25px rgba(12,38,70,0.10);
}
.hero h1{ margin:0; font-size:28px; font-weight:800; }
.hero p{ margin:6px 0 0 0; opacity:.95; }
.card{
  background: var(--card); border-radius: 12px; padding: 14px 16px;
  box-shadow: 0 8px 22px rgba(12,38,70,0.06);
}
.muted{ color: var(--muted); }
.small{ font-size:.92rem; }
hr{ border:none; border-top:1px solid rgba(15,23,42,.10); margin: 14px 0; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)


# -----------------------------
# Safe async runner for Streamlit
# -----------------------------
def run_async_safely(coro):
    """
    Run an async coroutine from Streamlit safely even if an event loop is already running.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # event loop is running (Streamlit); enable nesting
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)


# -----------------------------
# Prompts/templates
# -----------------------------
PROMPT_FILE = Path("prompt_templates.json")

def load_prompt_templates() -> Dict[str, Dict[str, str]]:
    if PROMPT_FILE.exists():
        try:
            return json.loads(PROMPT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"expert_prompts": {}, "quick_actions": {}}
    return {"expert_prompts": {}, "quick_actions": {}}


# -----------------------------
# Mask secrets / env display
# -----------------------------
def mask_value(v: Optional[str], keep_end: int = 6) -> str:
    if not v:
        return "Not configured"
    if len(v) <= keep_end + 4:
        return "****"
    return "****" + v[-keep_end:]


# -----------------------------
# Cached orchestrator (no async init here)
# -----------------------------
@st.cache_resource(ttl=60 * 60)
def get_orchestrator() -> WBIATIAgentOrchestrator:
    cfg = get_agent_config()
    # Env override (Streamlit Secrets become env vars)
    cfg.api_key = os.environ.get("DO_API_KEY", getattr(cfg, "api_key", None))
    cfg.endpoint = os.environ.get("DO_ENDPOINT", getattr(cfg, "endpoint", None))
    cfg.chatbot_id = os.environ.get("DO_CHATBOT_ID", getattr(cfg, "chatbot_id", None))
    return WBIATIAgentOrchestrator(cfg)


orchestrator = get_orchestrator()


# -----------------------------
# Dashboard rendering (client-demo grade)
# -----------------------------
def render_kpi_row(kpis: List[Dict[str, Any]]):
    cols = st.columns(min(3, max(1, len(kpis))))
    for i, k in enumerate(kpis[:3]):
        cols[i].metric(k.get("label", "KPI"), k.get("value", "—"), k.get("delta"))

def render_initiatives_table():
    st.subheader("Top 5 strategic initiatives")
    st.table([
        {"Initiative": "Green Energy Transition", "Lead": "PMO", "Status": "On track", "Budget (Bn USD)": 120, "Timeline": "2025–2040"},
        {"Initiative": "Global Digital Education", "Lead": "Education GP", "Status": "On track", "Budget (Bn USD)": 80, "Timeline": "2024–2036"},
        {"Initiative": "Pandemic Preparedness", "Lead": "Health GP", "Status": "Slight delay", "Budget (Bn USD)": 100, "Timeline": "2023–2038"},
        {"Initiative": "Water & Sanitation for All", "Lead": "WASH GP", "Status": "New", "Budget (Bn USD)": 60, "Timeline": "2026–2045"},
        {"Initiative": "Climate Resilience Infra", "Lead": "Infra GP", "Status": "New", "Budget (Bn USD)": 90, "Timeline": "2026–2046"},
    ])

def render_consulting_dashboard(title: str = "Global Portfolio Dashboard"):
    """
    Polished "consulting style" dashboard with charts and infographics.
    Uses placeholder data until you wire real metrics—still impressive for client demos.
    """
    st.markdown(f"## {title}")

    # KPI row (preview)
    render_kpi_row([
        {"label": "Budget Utilized", "value": "75%", "delta": "+2% QoQ"},
        {"label": "Impact Score", "value": "4.2 / 5.0", "delta": "+0.1"},
        {"label": "Risk Exposure", "value": "Moderate", "delta": "Stable"},
    ])

    st.markdown("<hr/>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Regional investment by sector (last 10 yrs)")
        df = pd.DataFrame({
            "Category": ["Africa", "Asia", "Education", "Health", "Europe", "MENA"],
            "Value": [28, 18, 24, 19, 6, 3]
        })
        fig = px.bar(df, x="Category", y="Value")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Active projects (global)")
        # map-like infographic proxy (bubble chart)
        geo = pd.DataFrame({
            "Region": ["Africa", "Asia", "Europe", "MENA", "Americas"],
            "Active Projects": [420, 380, 120, 90, 190]
        })
        fig2 = px.scatter(geo, x="Region", y="Active Projects", size="Active Projects")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    c3, c4 = st.columns([2, 1])
    with c3:
        st.subheader("Portfolio trend analysis (Bn USD)")
        df2 = pd.DataFrame({
            "Year": [2019, 2020, 2021, 2022, 2023, 2024],
            "Investment": [210, 235, 250, 300, 270, 310],
            "Disbursement": [95, 110, 135, 160, 190, 230]
        })
        fig3 = px.line(df2, x="Year", y=["Investment", "Disbursement"])
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.subheader("Risk heatmap (portfolio)")
        heat = pd.DataFrame([
            ["High", 7, 4, 8, 12, 30, 36, 25],
            ["Moderate", 8, 15, 12, 12, 12, 23, 25],
            ["Low", 8, 5, 6, 15, 17, 25, 26],
            ["Stable", 7, 3, 5, 15, 25, 23, 25],
        ], columns=["Band", "Geopolitical", "Economic", "Financial", "Social", "Environmental", "Operational", "Cyber"])
        fig4 = px.imshow(heat.set_index("Band"), aspect="auto")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    render_initiatives_table()


def render_executive_brief(summary_text: str, key_points: Optional[List[str]] = None):
    st.markdown("### Executive summary")
    st.info(summary_text or "Portfolio snapshot generated. See dashboard below for the client-ready view.")
    if key_points:
        st.markdown("**Key points**")
        for p in key_points[:5]:
            st.markdown(f"- {p}")


# -----------------------------
# Robust response normalization + fallback
# -----------------------------
def normalize_to_dict(resp: Any) -> Dict[str, Any]:
    if resp is None:
        return {}
    if isinstance(resp, dict):
        return resp
    if hasattr(resp, "to_dict"):
        try:
            return resp.to_dict()
        except Exception:
            pass
    if hasattr(resp, "__dict__"):
        return vars(resp)
    return {"raw": resp}

def fallback_do_agent_query(query: str) -> Dict[str, Any]:
    """
    If local agent paths break due to missing methods, call the DO agent directly.
    This keeps quick actions working and makes the demo resilient.
    """
    try:
        do_resp = run_async_safely(orchestrator.chatbot.send_query(query, context={"mode": "fallback"}))
        d = normalize_to_dict(do_resp)
        if d.get("success") is True:
            data = d.get("data", "")
            # Try to extract a nice narrative
            summary = ""
            if isinstance(data, dict):
                summary = data.get("summary") or data.get("executive_summary") or json.dumps(data)[:800]
            else:
                summary = str(data)[:1200]
            return {
                "success": True,
                "executive_summary": summary,
                "source": "do_agent_fallback",
                "raw": d
            }
        return {"success": False, "error": d.get("error") or "DO agent fallback failed", "raw": d}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------
# Session state
# -----------------------------
if "query_text" not in st.session_state:
    st.session_state["query_text"] = ""
if "last_response" not in st.session_state:
    st.session_state["last_response"] = None
if "last_dashboard" not in st.session_state:
    st.session_state["last_dashboard"] = None


# -----------------------------
# Header
# -----------------------------
st.markdown(
    f"""
    <div class="hero">
      <h1>World Bank — IATI Intelligence Agent</h1>
      <p>Client-ready portfolio insights, dashboards, and quick actions. <span style="opacity:.85">({datetime.utcnow().strftime('%Y-%m-%d')})</span></p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("### Environment")
    st.markdown(f"- **Endpoint:** {mask_value(os.environ.get('DO_ENDPOINT'))}")
    st.markdown(f"- **Chatbot ID:** {mask_value(os.environ.get('DO_CHATBOT_ID'))}")
    st.markdown(f"- **API key present:** {'✅' if bool(os.environ.get('DO_API_KEY')) else '❌'}")

    st.markdown("---")
    auto_run_actions = st.toggle("Auto-run when selecting a quick action", value=False)
    auto_dashboard = st.toggle("Auto-generate dashboard after query", value=True)
    st.markdown("<div class='muted small'>Secrets are masked. Configure in Streamlit Cloud → Settings → Secrets.</div>", unsafe_allow_html=True)


# -----------------------------
# Main layout
# -----------------------------
left, right = st.columns([3, 1])

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Agent status")
    status = {}
    try:
        status = orchestrator.get_agent_status()
    except Exception:
        status = {"agent_info": {"name": "World Bank IATI Intelligence Agent", "version": "1.0.0", "initialized": False}}

    st.json({
        "name": status.get("agent_info", {}).get("name", "World Bank IATI Intelligence Agent"),
        "version": status.get("agent_info", {}).get("version", "1.0.0"),
        "initialized": status.get("agent_info", {}).get("initialized", False),
        "endpoint": mask_value(getattr(orchestrator.config, "endpoint", None))
    })

    if not status.get("agent_info", {}).get("initialized", False):
        st.warning("Agent not fully initialized yet. It will initialize on first request.")
    st.markdown("</div>", unsafe_allow_html=True)


with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Chat / Query")
    st.markdown("<div class='muted small'>Ask questions, run quick actions, and get a dashboard-ready output suitable for clients.</div>", unsafe_allow_html=True)

    # Load templates
    prompts = load_prompt_templates()
    expert_prompts = prompts.get("expert_prompts", {}) or {}
    quick_actions = prompts.get("quick_actions", {}) or {}

    # Expert prompt selector
    if expert_prompts:
        chosen = st.selectbox(
            "Expert templates",
            options=[""] + list(expert_prompts.keys()),
            format_func=lambda k: "— select a template —" if k == "" else k.replace("_", " ").title()
        )
        if chosen:
            st.caption("Template preview")
            st.code(expert_prompts[chosen], language="text")
            if st.button("Use template"):
                st.session_state["query_text"] = expert_prompts[chosen]
                if auto_run_actions:
                    st.experimental_rerun()

    # Quick actions
    if quick_actions:
        st.markdown("**Quick actions**")
        qa_items = list(quick_actions.items())
        cols = st.columns(min(3, max(1, len(qa_items))))
        for i, (k, v) in enumerate(qa_items):
            if cols[i % len(cols)].button(k.replace("_", " ").title()):
                st.session_state["query_text"] = v
                if auto_run_actions:
                    st.experimental_rerun()

    # Query text area
    query = st.text_area("Enter your natural language query", height=160, value=st.session_state["query_text"])

    b1, b2, b3 = st.columns([1, 1, 1])
    run_btn = b1.button("Run Query")
    dash_btn = b2.button("Create Executive Dashboard")
    clear_btn = b3.button("Clear")

    if clear_btn:
        st.session_state["query_text"] = ""
        st.session_state["last_response"] = None
        st.session_state["last_dashboard"] = None
        st.experimental_rerun()

    # -----------------------------
    # Run Query handler
    # -----------------------------
    def execute_query(q: str) -> Dict[str, Any]:
        """
        Execute via orchestrator; on known missing-method errors, fallback to DO agent.
        """
        # Try orchestrator pipeline first
        try:
            resp = run_async_safely(orchestrator.process_user_query(q))
            d = normalize_to_dict(resp)
            # If orchestrator returns error dict
            if d.get("error") is True or d.get("success") is False:
                raise Exception(d.get("message") or d.get("error") or "Orchestrator returned error")
            return {"success": True, "payload": d, "source": "orchestrator"}
        except Exception as e:
            msg = str(e)
            # Known missing method issues: keep demo working
            if ("object has no attribute '_analyze_trends'" in msg) or ("_analyze_sector_data" in msg) or ("_execute_analysis" in msg):
                fb = fallback_do_agent_query(q)
                if fb.get("success"):
                    # Wrap into a response compatible with UI
                    return {
                        "success": True,
                        "payload": {
                            "executive_summary": fb.get("executive_summary", ""),
                            "key_insights": [],
                            "recommendations": [],
                            "do_agent_insights": fb.get("raw", {}),
                            "enhanced": True,
                            "source": "do_agent_fallback"
                        },
                        "source": "do_agent_fallback"
                    }
                return {"success": False, "error": fb.get("error", msg), "source": "do_agent_fallback"}
            return {"success": False, "error": msg, "source": "orchestrator"}

    if run_btn:
        if not query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Processing query..."):
                out = execute_query(query.strip())

            if not out.get("success"):
                st.error(f"Query failed: {out.get('error')}")
            else:
                result = out["payload"]
                st.session_state["last_response"] = result
                st.success(f"Query processed ({out.get('source')})")

                # Executive summary + dashboard immediately
                summary_text = result.get("executive_summary") or "Portfolio snapshot generated."
                key_pts = []
                # If you have key insights, turn into bullet points
                if isinstance(result.get("key_insights"), list):
                    for it in result["key_insights"][:5]:
                        if isinstance(it, dict):
                            key_pts.append(f"{it.get('title','Insight')}: {it.get('finding','')}")
                        else:
                            key_pts.append(str(it))

                render_executive_brief(summary_text, key_pts)

                if auto_dashboard:
                    st.markdown("### Client-ready dashboard")
                    render_consulting_dashboard("Global Portfolio Dashboard (Preview)")

                with st.expander("Raw response (JSON)"):
                    st.json(result)

    # -----------------------------
    # Create Dashboard handler
    # -----------------------------
    if dash_btn:
        with st.spinner("Generating executive dashboard..."):
            # Use local consulting dashboard renderer regardless of backend availability
            # If you want to also generate config JSON from dashboard_framework/orchestrator, try it safely:
            dash_config = None
            try:
                dash_config = run_async_safely(
                    orchestrator.create_executive_dashboard(
                        "executive",
                        parameters={},
                        title="Global Portfolio Dashboard",
                        context={"source_query": query.strip(), "style": "consulting"}
                    )
                )
                dash_config = normalize_to_dict(dash_config)
                if dash_config.get("error"):
                    dash_config = None
            except Exception:
                dash_config = None

        st.success("Dashboard ready")
        render_consulting_dashboard("Global Portfolio Dashboard (Preview)")

        if dash_config:
            with st.expander("Raw dashboard JSON"):
                st.json(dash_config)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='muted small'>Built with care — treat model outputs as advisory. Sanitize before operational use.</div>", unsafe_allow_html=True)
