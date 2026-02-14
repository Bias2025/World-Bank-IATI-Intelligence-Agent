# streamlit_app.py
"""
Streamlit app (client-demo ready) using REAL DO Agent knowledge-base outputs.

Key updates:
- Calls DO agent correctly via do_api_integration.ChatbotInterface (/api/v1/chat/completions)
- Extracts a structured `metrics` JSON block from the assistant content (if present)
- Renders dashboard charts using those metrics (not placeholders), falling back gracefully
- Multi-color palette + risk heatmap with legend/colorbar
- Quick actions work consistently (no dependency on missing local agent methods)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from wb_iati_agent_config import get_agent_config
from do_api_integration import ChatbotInterface, extract_json_block


# -----------------------------
# Styling + palette
# -----------------------------
st.set_page_config(page_title="WB IATI Intelligence Agent", layout="wide")

THEME = {
    "bg": "#F7FAFC",
    "panel": "#FFFFFF",
    "muted": "#5B6B84",
    "border": "rgba(15, 23, 42, 0.10)",
    "teal": "#14B8A6",
    "cyan": "#22D3EE",
    "sky": "#38BDF8",
    "lav": "#C4B5FD",
    "violet": "#8B5CF6",
    "indigo": "#4F46E5",
    "blueviolet": "#6366F1",
}

PALETTE = [THEME["teal"], THEME["cyan"], THEME["sky"], THEME["lav"], THEME["violet"], THEME["indigo"], THEME["blueviolet"]]
RISK_COLORSCALE = [
    [0.00, THEME["teal"]],
    [0.25, THEME["cyan"]],
    [0.50, THEME["sky"]],
    [0.75, THEME["lav"]],
    [1.00, THEME["indigo"]],
]

st.markdown(
    f"""
<style>
html,body,[data-testid="stAppViewContainer"]{{ background:{THEME["bg"]}; }}
.hero{{
  background: linear-gradient(90deg, rgba(20,184,166,0.14), rgba(34,211,238,0.12), rgba(56,189,248,0.10), rgba(139,92,246,0.10));
  border: 1px solid {THEME["border"]};
  border-radius: 18px;
  padding: 18px 18px 10px 18px;
  box-shadow: 0 10px 30px rgba(2,6,23,0.06);
}}
.card{{
  background:{THEME["panel"]};
  border: 1px solid {THEME["border"]};
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(2,6,23,0.06);
}}
.muted{{ color:{THEME["muted"]}; }}
</style>
""",
    unsafe_allow_html=True,
)

def mask(v: Optional[str], keep: int = 6) -> str:
    if not v:
        return "Not set"
    if len(v) <= keep + 4:
        return "****"
    return "****" + v[-keep:]


# -----------------------------
# Cached DO interface
# -----------------------------
@st.cache_resource(ttl=60 * 30)
def get_chatbot() -> ChatbotInterface:
    cfg = get_agent_config()
    # Ensure secrets can override config
    cfg.endpoint = os.environ.get("DO_ENDPOINT", getattr(cfg, "endpoint", ""))
    cfg.api_key = os.environ.get("DO_API_KEY", getattr(cfg, "api_key", ""))
    cfg.chatbot_id = os.environ.get("DO_CHATBOT_ID", getattr(cfg, "chatbot_id", None))
    return ChatbotInterface(cfg)

chatbot = get_chatbot()


# -----------------------------
# Quick actions
# -----------------------------
QUICK_ACTIONS: Dict[str, str] = {
    "Portfolio overview": "Analyze overall World Bank portfolio performance including disbursement efficiency, sector distribution, and regional allocation. Provide executive-level insights with key metrics and trends.",
    "Sector analysis": "Analyze commitments and disbursements by sector. Provide top sectors, growth sectors, and underfunded sectors with numbers and percentages.",
    "Geographic analysis": "Analyze portfolio distribution by region and top countries. Provide regional totals and identify concentration risks.",
    "Trend analysis": "Conduct a trend analysis of commitments and disbursements over time for at least 5 years. Identify inflection points and drivers.",
    "Risk assessment": "Perform a portfolio risk assessment and return a risk matrix by region and risk level (Low/Moderate/High) with numeric scores.",
}


# -----------------------------
# Metrics mapping helpers
# -----------------------------
def ensure_df(obj: Any, cols: List[str]) -> Optional[pd.DataFrame]:
    if obj is None:
        return None
    try:
        df = pd.DataFrame(obj)
        # soft check
        for c in cols:
            if c not in df.columns:
                return None
        return df
    except Exception:
        return None


def render_kpis(metrics: Dict[str, Any]):
    k = metrics.get("kpis") or {}
    c1, c2, c3 = st.columns(3)
    c1.metric("Budget Utilized", f'{k.get("budget_utilized_pct","—")}%' if "budget_utilized_pct" in k else "—")
    c2.metric("Impact Score", str(k.get("impact_score","—")))
    c3.metric("Risk Exposure", str(k.get("risk_exposure","—")))


def fig_risk_heatmap(df: pd.DataFrame) -> go.Figure:
    # Expected: rows RiskLevel, columns are regions with numeric scores 0..100
    df = df.copy()
    risk_levels = df["RiskLevel"].tolist()
    regions = [c for c in df.columns if c != "RiskLevel"]
    z = df[regions].values

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=regions,
            y=risk_levels,
            colorscale=RISK_COLORSCALE,
            colorbar=dict(
                title="Risk score",
                tickmode="array",
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["0", "25", "50", "75", "100"],
                len=0.8,
            ),
            zmin=0,
            zmax=100,
            hovertemplate="Region=%{x}<br>Risk=%{y}<br>Score=%{z}<extra></extra>",
        )
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
    return fig


# -----------------------------
# UI
# -----------------------------
st.markdown(
    """
<div class="hero">
  <div style="font-size:22px; font-weight:800;">World Bank — IATI Intelligence Agent</div>
  <div class="muted">Uses the DO knowledge base via <code>/api/v1/chat/completions</code> and renders real metrics when returned.</div>
</div>
""",
    unsafe_allow_html=True,
)
st.write("")

with st.sidebar:
    st.markdown("### Environment")
    st.markdown(f"- **Endpoint:** {mask(os.environ.get('DO_ENDPOINT'))}")
    st.markdown(f"- **Chatbot ID:** {mask(os.environ.get('DO_CHATBOT_ID'))}")
    st.markdown(f"- **API key present:** {'✅' if bool(os.environ.get('DO_API_KEY')) else '❌'}")
    auto_dashboard = st.toggle("Auto-dashboard after query", value=True)
    show_raw = st.toggle("Show raw JSON", value=False)

left, right = st.columns([3, 1])

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Quick actions")
    for k in QUICK_ACTIONS.keys():
        if st.button(k, use_container_width=True):
            st.session_state["query_text"] = QUICK_ACTIONS[k]
    st.markdown("</div>", unsafe_allow_html=True)

with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Chat / Query")
    st.session_state.setdefault("query_text", QUICK_ACTIONS["Portfolio overview"])
    query = st.text_area("Enter your request", value=st.session_state["query_text"], height=160)
    run_btn = st.button("Run Query", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

if run_btn:
    st.session_state["query_text"] = query
    with st.spinner("Calling DO agent..."):
        resp = st.session_state["last_resp"] = st.runtime.scriptrunner.add_script_run_ctx  # no-op placeholder to avoid lint
        # Real call (async wrapper exists in ChatbotInterface methods, but our internal client is sync)
        # We can call it via asyncio since ChatbotInterface is async; easiest is to run it via a tiny loop:
        import asyncio
        try:
            do_resp = asyncio.run(chatbot.send_query(query))
        except RuntimeError:
            # Streamlit running loop: use nest_asyncio
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            do_resp = loop.run_until_complete(chatbot.send_query(query))

    if not do_resp.success:
        st.error(f"DO Agent call failed (status={do_resp.status_code}): {do_resp.error}")
        st.caption(f"URL used: {do_resp.url}")
        if show_raw:
            st.json(do_resp.to_dict())
    else:
        st.success(f"Query processed (status={do_resp.status_code}, {do_resp.execution_time:.2f}s)")

        # Extract assistant answer
        assistant_text = do_resp.text or ""
        st.markdown("### Executive summary")
        st.info(assistant_text[:1200] if assistant_text else "Response received.")

        # Extract metrics JSON block from assistant message
        metrics = extract_json_block(assistant_text)
        if isinstance(metrics, dict) and ("regional_investment_by_sector" in metrics or "portfolio_trend" in metrics or "risk_heatmap" in metrics):
            st.markdown("### Client-ready dashboard")
            render_kpis(metrics)

            c1, c2 = st.columns(2)

            df_reg = ensure_df(metrics.get("regional_investment_by_sector"), ["Category", "Value"])
            if df_reg is not None:
                with c1:
                    fig = px.bar(df_reg, x="Category", y="Value", color="Category", color_discrete_sequence=PALETTE,
                                 title="Regional investment by sector")
                    fig.update_layout(showlegend=False, height=360, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                with c1:
                    st.warning("No structured regional investment data returned.")

            df_active = ensure_df(metrics.get("active_projects_global"), ["Region", "ActiveProjects"])
            if df_active is not None:
                with c2:
                    size_col = "AvgCommitmentUSDm" if "AvgCommitmentUSDm" in df_active.columns else None
                    fig = px.scatter(
                        df_active,
                        x="Region",
                        y="ActiveProjects",
                        size=size_col,
                        color="Region",
                        color_discrete_sequence=PALETTE,
                        title="Active projects (global)",
                        size_max=42,
                    )
                    fig.update_layout(showlegend=False, height=360, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                with c2:
                    st.warning("No structured active projects data returned.")

            c3, c4 = st.columns(2)

            df_trend = ensure_df(metrics.get("portfolio_trend"), ["Year", "InvestmentBn", "DisbursementBn"])
            if df_trend is not None:
                with c3:
                    m = df_trend.melt(id_vars=["Year"], value_vars=["InvestmentBn", "DisbursementBn"], var_name="Series", value_name="BnUSD")
                    fig = px.line(m, x="Year", y="BnUSD", color="Series",
                                  color_discrete_sequence=[THEME["indigo"], THEME["teal"]],
                                  title="Portfolio trend analysis (Bn USD)", markers=True)
                    fig.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                with c3:
                    st.warning("No structured trend data returned.")

            df_risk = ensure_df(metrics.get("risk_heatmap"), ["RiskLevel"])
            if df_risk is not None:
                with c4:
                    st.plotly_chart(fig_risk_heatmap(df_risk), use_container_width=True)
            else:
                with c4:
                    st.warning("No structured risk heatmap returned.")

        else:
            st.warning(
                "The agent response did not include a parseable ` ```json ... ``` ` metrics block yet. "
                "Ask the agent to include one (the system prompt already requests it)."
            )

        if show_raw:
            st.markdown("### Raw response JSON")
            st.json(do_resp.to_dict())
            if do_resp.data:
                st.markdown("### DO chat.completion payload")
                st.json(do_resp.data)

st.caption("Built with care — treat model outputs as advisory. Sanitize before operational use.")
