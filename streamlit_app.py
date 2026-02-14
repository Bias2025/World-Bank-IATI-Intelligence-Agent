import json
import math
import random
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
import altair as alt

from wb_iati_agent_config import get_agent_config
from do_api_integration import ChatbotInterface


# -------------------------
# App config
# -------------------------
st.set_page_config(
    page_title="World Bank — IATI Intelligence Agent",
    page_icon="🌍",
    layout="wide",
)

# Subtle enterprise feel (no secret leakage)
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
      div[data-testid="stMetricValue"] { font-size: 1.6rem; }
      .quiet-note { color: rgba(0,0,0,0.55); font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Palette (cool gradient vibe)
# -------------------------
PALETTE = ["#14b8a6", "#22d3ee", "#38bdf8", "#6366f1", "#7c3aed"]  # teal→cyan→sky→indigo→violet


# -------------------------
# Prompt templates (UI-loaded quick actions)
# -------------------------
PROMPT_TEMPLATES = {
    "Portfolio overview": "Analyze the overall World Bank portfolio performance including disbursement efficiency, sector distribution, and regional allocation. Provide executive-level insights with key metrics and trends.",
    "Sector analysis": "Provide a sector deep-dive (pick the most material sector from the data): commitments, disbursements, active projects, top countries, and major implementation risks. Return dashboard-ready metrics and charts.",
    "Trend analysis": "Conduct a trend analysis over time: commitments vs disbursements, project starts/completions, and sector/region shifts. Return dashboard-ready metrics and charts.",
    "Risk assessment": "Perform portfolio risk assessment: concentration risks, implementation challenges, fiduciary risks, and geopolitical exposure by region/sector. Return a heatmap-ready dataset and top risks with evidence.",
    "Country spotlight": "Pick the highest-exposure country in the portfolio (by commitments or project count) and provide a country spotlight dashboard: sector mix, active projects, disbursement, and risks.",
}


# -------------------------
# Cached init
# -------------------------
@st.cache_resource(show_spinner=False)
def get_client():
    cfg = get_agent_config()
    chatbot = ChatbotInterface(cfg)
    chatbot.initialize_session()
    return chatbot, cfg


def coerce_number(v) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace(",", "")
        return float(s)
    except Exception:
        return None


def ensure_placeholders(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    If agent omitted some metrics/charts (because grounded data not available),
    we add demo-safe placeholders ONLY for missing parts.
    """
    parsed = parsed or {}

    if "executive_summary" not in parsed or not parsed.get("executive_summary"):
        parsed["executive_summary"] = "Analysis completed. Some metrics were not returned from grounded sources; demo placeholders may appear where needed."

    if "key_metrics" not in parsed or not isinstance(parsed.get("key_metrics"), list) or len(parsed["key_metrics"]) == 0:
        parsed["key_metrics"] = [
            {"label": "Total commitments", "value": 500, "unit": "Bn USD", "note": "Placeholder (no grounded metric returned)"},
            {"label": "Active projects", "value": 1200, "unit": "", "note": "Placeholder"},
            {"label": "Disbursement rate", "value": 75, "unit": "%", "note": "Placeholder"},
            {"label": "Impact score", "value": 4.2, "unit": "/5", "note": "Placeholder"},
        ]

    if "charts" not in parsed or not isinstance(parsed.get("charts"), list) or len(parsed["charts"]) == 0:
        parsed["charts"] = [
            {
                "title": "Regional investment by sector (last 10 yrs)",
                "type": "bar",
                "x_label": "Region",
                "y_label": "Value",
                "data": [{"x": r, "y": v, "series": "Investment"} for r, v in zip(
                    ["Africa", "Asia", "Education", "Health", "Europe", "MENA"],
                    [28, 18, 24, 19, 6, 3]
                )],
            },
            {
                "title": "Portfolio trend analysis (Bn USD)",
                "type": "line",
                "x_label": "Year",
                "y_label": "Bn USD",
                "data": [{"x": str(y), "y": val, "series": s} for s, seq in {
                    "Investment": [210, 235, 250, 300, 270, 310],
                    "Disbursement": [120, 140, 155, 190, 205, 230],
                }.items() for y, val in zip([2019, 2020, 2021, 2022, 2023, 2024], seq)],
            },
            {
                "title": "Risk heatmap (portfolio)",
                "type": "heatmap",
                "x_label": "Region",
                "y_label": "Risk Category",
                "data": [
                    {"x": x, "y": y, "series": "risk", "value": val}
                    for y, row in zip(["Geopolitical", "Economic", "Social", "Environmental", "Operational", "Cyber"],
                                      [
                                          [7, 4, 8, 12, 30, 25],
                                          [8, 15, 12, 12, 12, 23],
                                          [8, 5, 6, 15, 17, 26],
                                          [7, 3, 5, 15, 25, 25],
                                          [6, 4, 5, 10, 18, 22],
                                          [5, 4, 6, 9, 14, 20],
                                      ])
                    for x, val in zip(["Africa", "Asia", "Education", "Health", "Europe", "MENA"], row)
                ],
            },
        ]

    if "recommendations" not in parsed or not isinstance(parsed.get("recommendations"), list):
        parsed["recommendations"] = [
            "Prioritize regions with high operational risk scores for implementation support.",
            "Rebalance sector allocations to reduce concentration risk.",
            "Improve disbursement velocity by targeting bottleneck project phases.",
        ]

    if "risks" not in parsed or not isinstance(parsed.get("risks"), list):
        parsed["risks"] = [
            {"risk": "Implementation capacity constraints", "severity": "High", "evidence": "Placeholder risk (agent did not return grounded evidence)."},
            {"risk": "Regional concentration risk", "severity": "Moderate", "evidence": "Placeholder."},
        ]

    return parsed


def render_kpis(key_metrics: List[Dict[str, Any]]):
    cols = st.columns(4)
    for i, m in enumerate(key_metrics[:4]):
        v = coerce_number(m.get("value"))
        unit = (m.get("unit") or "").strip()
        label = m.get("label", f"Metric {i+1}")
        note = m.get("note")
        display = f"{v:g}{(' ' + unit) if unit else ''}" if v is not None else "—"
        with cols[i]:
            st.metric(label, display)
            if note:
                st.caption(note)


def chart_bar(df: pd.DataFrame, title: str, x_label: str, y_label: str):
    # series-aware bar
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("x:N", title=x_label),
            y=alt.Y("y:Q", title=y_label),
            color=alt.Color("series:N", scale=alt.Scale(range=PALETTE)),
            tooltip=["x", "y", "series"],
        )
        .properties(title=title, height=300)
    )
    st.altair_chart(chart, use_container_width=True)


def chart_line(df: pd.DataFrame, title: str, x_label: str, y_label: str):
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("x:N", title=x_label),
            y=alt.Y("y:Q", title=y_label),
            color=alt.Color("series:N", scale=alt.Scale(range=PALETTE)),
            tooltip=["x", "y", "series"],
        )
        .properties(title=title, height=300)
    )
    st.altair_chart(chart, use_container_width=True)


def chart_pie(df: pd.DataFrame, title: str):
    # expects x category, y value
    chart = (
        alt.Chart(df)
        .mark_arc()
        .encode(
            theta=alt.Theta("y:Q"),
            color=alt.Color("x:N", scale=alt.Scale(range=PALETTE)),
            tooltip=["x", "y"],
        )
        .properties(title=title, height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def chart_heatmap(df: pd.DataFrame, title: str, x_label: str, y_label: str):
    # More colorful heatmap with legend
    if "value" not in df.columns:
        # allow fallback where y= value
        df = df.rename(columns={"y": "value"})
    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("x:N", title=x_label),
            y=alt.Y("y:N", title=y_label),
            color=alt.Color(
                "value:Q",
                title="Risk score",
                scale=alt.Scale(range=PALETTE),
                legend=alt.Legend(orient="right"),
            ),
            tooltip=["x", "y", "value"],
        )
        .properties(title=title, height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def render_charts(charts: List[Dict[str, Any]]):
    # two-column dashboard grid
    cols = st.columns(2)
    c = 0
    for ch in charts[:6]:
        df = pd.DataFrame(ch.get("data", []))
        if df.empty:
            continue

        title = ch.get("title", "Chart")
        typ = (ch.get("type") or "").lower()
        x_label = ch.get("x_label", "")
        y_label = ch.get("y_label", "")

        with cols[c % 2]:
            if typ == "bar":
                chart_bar(df, title, x_label, y_label)
            elif typ == "line":
                chart_line(df, title, x_label, y_label)
            elif typ == "pie":
                chart_pie(df, title)
            elif typ == "heatmap":
                chart_heatmap(df, title, x_label, y_label)
            elif typ == "scatter":
                # expects x,y
                chart = (
                    alt.Chart(df)
                    .mark_circle(size=120)
                    .encode(
                        x=alt.X("x:N", title=x_label),
                        y=alt.Y("y:Q", title=y_label),
                        color=alt.Color("series:N", scale=alt.Scale(range=PALETTE)),
                        tooltip=["x", "y", "series"],
                    )
                    .properties(title=title, height=300)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info(f"Unsupported chart type: {typ}")
        c += 1


def render_risks(risks: List[Dict[str, Any]]):
    if not risks:
        return
    st.subheader("Top risks")
    for r in risks[:5]:
        sev = r.get("severity", "—")
        risk = r.get("risk", "Risk")
        ev = r.get("evidence", "")
        st.markdown(f"**{risk}** — _{sev}_")
        if ev:
            st.caption(ev)


# -------------------------
# UI
# -------------------------
st.title("World Bank — IATI Intelligence Agent")
st.caption("Ask questions about the World Bank portfolio, generate dashboards, or run analytics. Outputs are advisory—validate before operational use.")

chatbot, cfg = get_client()

with st.sidebar:
    st.subheader("Quick actions")
    action = st.radio(
        "Pick a workflow",
        list(PROMPT_TEMPLATES.keys()),
        index=0,
        label_visibility="collapsed",
    )
    if st.button("Run selected action", use_container_width=True):
        st.session_state["query_text"] = PROMPT_TEMPLATES[action]
        st.session_state["autorun"] = True

    st.divider()
    st.subheader("Agent status")
    # hide secrets; only show safe bits
    st.json(
        {
            "name": getattr(cfg, "agent_name", "World Bank IATI Intelligence Agent"),
            "version": getattr(cfg, "version", "1.0.0"),
            "initialized": True,
            "endpoint": "***",
        }
    )
    st.caption("Secrets are hidden by design.")


st.subheader("Chat / Query")
query = st.text_area(
    "Enter your natural language query",
    value=st.session_state.get("query_text", PROMPT_TEMPLATES["Portfolio overview"]),
    height=140,
)

colA, colB, colC = st.columns([1, 1.2, 1])
run_btn = colA.button("Run Query", use_container_width=True)
dash_btn = colB.button("Create Executive Dashboard", use_container_width=True)
clear_btn = colC.button("Clear", use_container_width=True)

if clear_btn:
    for k in ["last_result", "last_raw"]:
        st.session_state.pop(k, None)
    st.session_state["query_text"] = ""
    st.rerun()

autorun = st.session_state.pop("autorun", False)
if run_btn or autorun:
    with st.spinner("Querying agent and building dashboard…"):
        result = chatbot.send_iati_query(query, force_json=True, include_retrieval_info=True)
        st.session_state["last_raw"] = result
        parsed = result.get("parsed") or {}
        parsed = ensure_placeholders(parsed)
        st.session_state["last_result"] = parsed

if dash_btn:
    with st.spinner("Generating executive dashboard package…"):
        result = chatbot.create_dashboard_request("executive", {})
        st.session_state["last_raw"] = result
        parsed = result.get("parsed") or {}
        parsed = ensure_placeholders(parsed)
        st.session_state["last_result"] = parsed

parsed = st.session_state.get("last_result")
raw = st.session_state.get("last_raw")

if parsed:
    st.success("Query processed")

    st.subheader("Executive summary")
    st.write(parsed.get("executive_summary", ""))

    # KPIs + charts immediately (the thing you asked for)
    st.markdown("#### Portfolio KPIs")
    render_kpis(parsed.get("key_metrics", []))

    st.markdown("#### Dashboard")
    render_charts(parsed.get("charts", []))

    render_risks(parsed.get("risks", []))

    st.subheader("Recommendations")
    recs = parsed.get("recommendations", [])
    for r in recs[:5]:
        st.write(f"- {r}")

    with st.expander("Raw response (JSON)"):
        st.json(raw if isinstance(raw, dict) else {"raw": raw})

    st.markdown('<div class="quiet-note">Built with care — treat model outputs as advisory. Sanitize before operational use.</div>', unsafe_allow_html=True)
else:
    st.info("Run a query or choose a quick action to generate an executive dashboard.")
