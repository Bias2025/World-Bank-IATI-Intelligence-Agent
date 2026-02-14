# streamlit_app.py
# World Bank IATI Intelligence Agent — Streamlit UI (robust DO Agent integration + colorful charts)
#
# Key fixes:
# - Avoids "Event loop is closed" by using synchronous requests (no aiohttp/asyncio in UI layer)
# - Auto-discovers the DO Agent chat endpoint path (handles /chat 404s)
# - Prevents StreamlitAPIException: session_state cannot be modified after widget instantiation
# - Adds flexible "Quick Actions" that work for any prompt (not just portfolio overview)
# - Improves chart styling + risk heatmap with a multi-hue colorscale + legend/colorbar

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# -----------------------------
# Visual identity (cool gradients)
# -----------------------------
THEME = {
    "bg": "#F7FAFC",
    "panel": "#FFFFFF",
    "text": "#0B1220",
    "muted": "#5B6B84",
    "border": "rgba(15, 23, 42, 0.10)",
    # Palette: Teal → Cyan → Sky Blue; Lavender → Violet → Soft Purple; Indigo → Blue-Violet
    "teal": "#14B8A6",
    "cyan": "#22D3EE",
    "sky": "#38BDF8",
    "lav": "#C4B5FD",
    "violet": "#8B5CF6",
    "purple": "#A78BFA",
    "indigo": "#4F46E5",
    "blueviolet": "#6366F1",
}

PLOTLY_QUAL_SEQ = [
    THEME["teal"],
    THEME["cyan"],
    THEME["sky"],
    THEME["lav"],
    THEME["violet"],
    THEME["indigo"],
    THEME["blueviolet"],
    THEME["purple"],
]

# A custom colorscale for heatmaps (low -> high):
# teal -> cyan -> sky -> lavender -> violet -> indigo
RISK_COLORSCALE = [
    [0.00, THEME["teal"]],
    [0.20, THEME["cyan"]],
    [0.40, THEME["sky"]],
    [0.60, THEME["lav"]],
    [0.80, THEME["violet"]],
    [1.00, THEME["indigo"]],
]


# -----------------------------
# Streamlit setup + CSS
# -----------------------------
st.set_page_config(page_title="WB IATI Intelligence Agent", layout="wide")

st.markdown(
    f"""
<style>
    html, body, [class*="css"]  {{
        background: {THEME["bg"]};
        color: {THEME["text"]};
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
    }}
    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
    }}
    .app-hero {{
        background: linear-gradient(90deg, rgba(20,184,166,0.14), rgba(34,211,238,0.12), rgba(56,189,248,0.10), rgba(139,92,246,0.10));
        border: 1px solid {THEME["border"]};
        border-radius: 18px;
        padding: 18px 18px 10px 18px;
        box-shadow: 0 10px 30px rgba(2,6,23,0.06);
    }}
    .card {{
        background: {THEME["panel"]};
        border: 1px solid {THEME["border"]};
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(2,6,23,0.06);
    }}
    .muted {{
        color: {THEME["muted"]};
    }}
    .pill {{
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid {THEME["border"]};
        background: linear-gradient(90deg, rgba(99,102,241,0.12), rgba(167,139,250,0.12));
        font-size: 12px;
        color: {THEME["text"]};
        margin-right: 8px;
    }}
    .tiny {{
        font-size: 12px;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
def _now_ms() -> int:
    return int(time.time() * 1000)


def safe_json_loads(s: str) -> Optional[Any]:
    try:
        return json.loads(s)
    except Exception:
        return None


def extract_json_object(text: str) -> Optional[dict]:
    """
    Tries to extract a JSON object from a model response that includes prose + JSON.
    """
    if not text:
        return None
    # Look for the first {...} that parses.
    candidates = re.findall(r"\{(?:[^{}]|(?R))*\}", text, flags=re.DOTALL)
    for c in candidates:
        obj = safe_json_loads(c)
        if isinstance(obj, dict):
            return obj
    return None


def coerce_number(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace(",", "")
        try:
            return float(s)
        except Exception:
            return None
    return None


# -----------------------------
# DO Agent client (sync; endpoint discovery)
# -----------------------------
@dataclass
class DOAgentConfig:
    base_url: str
    chatbot_id: str
    api_key: str = ""  # optional, depending on your DO Agent auth
    timeout_s: int = 30


class DOAgentClient:
    """
    Synchronous client to call DigitalOcean Agents endpoint.
    Your logs show 404 at /capabilities and /chat, so we probe common routes.
    """

    COMMON_CHAT_PATHS = [
        "/chat",
        "/v1/chat",
        "/api/chat",
        "/agent/chat",
        "/agents/chat",
        "/v1/agents/chat",
        "/v1/agent/chat",
    ]

    def __init__(self, cfg: DOAgentConfig):
        self.cfg = cfg
        self._resolved_chat_path: Optional[str] = None
        self._last_probe: List[Tuple[str, int, str]] = []

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            # Adjust if your DO Agent expects a different header scheme
            h["Authorization"] = f"Bearer {self.cfg.api_key}"
        return h

    def probe_endpoints(self) -> List[Tuple[str, int, str]]:
        """
        Probes a few candidate endpoints and stores results.
        Returns list of (url, status_code, detail).
        """
        base = self.cfg.base_url.rstrip("/")
        results: List[Tuple[str, int, str]] = []
        payload = {
            "chatbot_id": self.cfg.chatbot_id,
            "message": "ping",
        }

        for path in self.COMMON_CHAT_PATHS:
            url = f"{base}{path}"
            try:
                r = requests.post(url, headers=self._headers(), json=payload, timeout=self.cfg.timeout_s)
                detail = ""
                try:
                    detail = r.text[:220]
                except Exception:
                    detail = ""
                results.append((url, r.status_code, detail))
            except Exception as e:
                results.append((url, -1, str(e)[:220]))

        self._last_probe = results

        # Pick the first 2xx as resolved chat path
        for url, status, _ in results:
            if 200 <= status < 300:
                self._resolved_chat_path = url.replace(base, "")
                break

        return results

    def chat(self, message: str, extra: Optional[dict] = None) -> Dict[str, Any]:
        """
        Calls the resolved chat endpoint (or probes first if unknown).
        Returns a dict: {ok, status, data, error, raw_text, url_used}
        """
        base = self.cfg.base_url.rstrip("/")
        if not self._resolved_chat_path:
            self.probe_endpoints()

        # Fallback: try /chat as default if nothing resolved
        path = self._resolved_chat_path or "/chat"
        url = f"{base}{path}"

        payload = {"chatbot_id": self.cfg.chatbot_id, "message": message}
        if extra:
            payload.update(extra)

        try:
            r = requests.post(url, headers=self._headers(), json=payload, timeout=self.cfg.timeout_s)
            raw_text = r.text or ""
            data = None
            try:
                data = r.json()
            except Exception:
                data = extract_json_object(raw_text)

            return {
                "ok": 200 <= r.status_code < 300,
                "status": r.status_code,
                "data": data,
                "raw_text": raw_text,
                "error": None if 200 <= r.status_code < 300 else raw_text[:400],
                "url_used": url,
            }
        except Exception as e:
            return {
                "ok": False,
                "status": -1,
                "data": None,
                "raw_text": "",
                "error": str(e),
                "url_used": url,
            }


# -----------------------------
# Local sample data (fallback)
# -----------------------------
def sample_portfolio_data() -> Dict[str, Any]:
    # Replace with your real parsed/aggregated data once DO returns structured values.
    return {
        "regional_investment_by_sector": pd.DataFrame(
            {
                "Category": ["Africa", "Asia", "Education", "Health", "Europe", "MENA"],
                "Value": [28, 18, 24, 19, 6, 3],
            }
        ),
        "active_projects_global": pd.DataFrame(
            {
                "Region": ["Africa", "Asia", "Europe", "MENA", "Americas"],
                "ActiveProjects": [420, 380, 120, 90, 190],
                "AvgCommitmentUSDm": [85, 92, 64, 58, 71],
            }
        ),
        "portfolio_trend": pd.DataFrame(
            {
                "Year": [2018, 2019, 2020, 2021, 2022, 2023],
                "InvestmentBn": [210, 235, 250, 300, 270, 312],
                "DisbursementBn": [160, 175, 190, 210, 205, 230],
            }
        ),
        # Risk heatmap scores 0..100
        "risk_heatmap": pd.DataFrame(
            {
                "RiskLevel": ["Low", "Moderate", "High"],
                "Africa": [25, 45, 70],
                "Asia": [20, 40, 65],
                "Europe": [15, 30, 50],
                "MENA": [22, 48, 72],
                "Americas": [18, 34, 55],
            }
        ),
    }


# -----------------------------
# Chart builders (colorful)
# -----------------------------
def fig_bar_regional(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df,
        x="Category",
        y="Value",
        color="Category",
        color_discrete_sequence=PLOTLY_QUAL_SEQ,
        title="Regional investment by sector (last 10 yrs)",
    )
    fig.update_layout(
        legend_title_text="Category",
        margin=dict(l=10, r=10, t=60, b=10),
        height=360,
        plot_bgcolor=THEME["panel"],
        paper_bgcolor=THEME["panel"],
    )
    return fig


def fig_bubble_active_projects(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="Region",
        y="ActiveProjects",
        size="AvgCommitmentUSDm",
        color="Region",
        color_discrete_sequence=PLOTLY_QUAL_SEQ,
        title="Active projects (global)",
        size_max=45,
    )
    fig.update_layout(
        legend_title_text="Region",
        margin=dict(l=10, r=10, t=60, b=10),
        height=360,
        plot_bgcolor=THEME["panel"],
        paper_bgcolor=THEME["panel"],
    )
    fig.update_yaxes(title="Active projects")
    fig.update_xaxes(title="Region")
    return fig


def fig_line_trend(df: pd.DataFrame) -> go.Figure:
    # Melt for multiseries
    m = df.melt(id_vars=["Year"], value_vars=["InvestmentBn", "DisbursementBn"], var_name="Series", value_name="BnUSD")
    fig = px.line(
        m,
        x="Year",
        y="BnUSD",
        color="Series",
        markers=True,
        color_discrete_sequence=[THEME["indigo"], THEME["teal"]],
        title="Portfolio trend analysis (Bn USD)",
    )
    fig.update_layout(
        legend_title_text="Series",
        margin=dict(l=10, r=10, t=60, b=10),
        height=360,
        plot_bgcolor=THEME["panel"],
        paper_bgcolor=THEME["panel"],
    )
    fig.update_yaxes(title="Bn USD")
    return fig


def fig_risk_heatmap(df: pd.DataFrame) -> go.Figure:
    # df format: RiskLevel + regions columns
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
                titleside="right",
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
    fig.update_layout(
        title="Risk heatmap (portfolio)",
        margin=dict(l=10, r=10, t=60, b=10),
        height=360,
        plot_bgcolor=THEME["panel"],
        paper_bgcolor=THEME["panel"],
    )
    return fig


# -----------------------------
# UI state (safe patterns)
# -----------------------------
def init_state():
    st.session_state.setdefault("query_text", "")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_backend", "Auto")
    st.session_state.setdefault("debug", False)
    st.session_state.setdefault("do_probe_results", [])
    st.session_state.setdefault("do_last_call", None)


def set_query_text(text: str):
    # Safe: update a separate state key that is NOT the widget key.
    st.session_state["query_text"] = text


def clear_query():
    st.session_state["query_text"] = ""


init_state()


# -----------------------------
# App header
# -----------------------------
st.markdown(
    """
<div class="app-hero">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:16px;">
    <div>
      <div style="font-size:22px; font-weight:700;">🌍 World Bank IATI Intelligence Agent</div>
      <div class="muted" style="margin-top:4px;">
        Executive dashboards + analysis powered by your DO knowledge base (with resilient fallbacks).
      </div>
    </div>
    <div>
      <span class="pill">Teal → Cyan → Sky</span>
      <span class="pill">Lavender → Violet</span>
      <span class="pill">Indigo accents</span>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")


# -----------------------------
# Sidebar: DO config + controls
# -----------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    default_base = os.environ.get("DO_AGENT_ENDPOINT", "https://mrngtcmmhzbbdopptwzoirop.agents.do-ai.run")
    default_chatbot = os.environ.get("DO_AGENT_CHATBOT_ID", "1FV8wQ78ZHOndsmrfmaNXmjpxi-snRAW")
    default_key = os.environ.get("DO_AGENT_API_KEY", "")

    base_url = st.text_input("DO Agent base URL", value=default_base)
    chatbot_id = st.text_input("Chatbot ID", value=default_chatbot)
    api_key = st.text_input("API Key (optional)", value=default_key, type="password")

    backend = st.selectbox("Backend", ["Auto", "DO knowledge base", "Local fallback"], index=0)
    st.session_state["last_backend"] = backend

    st.session_state["debug"] = st.toggle("Debug mode", value=st.session_state["debug"])

    st.write("")
    if st.button("🔌 Probe DO endpoints"):
        client = DOAgentClient(DOAgentConfig(base_url=base_url, chatbot_id=chatbot_id, api_key=api_key))
        st.session_state["do_probe_results"] = client.probe_endpoints()

    if st.session_state["do_probe_results"]:
        st.markdown("**Probe results**")
        for url, status, detail in st.session_state["do_probe_results"]:
            badge = "✅" if 200 <= status < 300 else ("⚠️" if status == -1 else "❌")
            st.caption(f"{badge} {status} — {url}")
            if st.session_state["debug"] and detail:
                st.code(detail, language="text")

    st.write("")
    st.markdown("---")
    st.markdown(
        "<div class='tiny muted'>Tip: If DO returns 404 on <code>/chat</code>, the correct route is likely different; probing helps you discover it.</div>",
        unsafe_allow_html=True,
    )


# -----------------------------
# Query execution
# -----------------------------
def run_query_via_do(message: str) -> Dict[str, Any]:
    client = DOAgentClient(DOAgentConfig(base_url=base_url, chatbot_id=chatbot_id, api_key=api_key))
    result = client.chat(message)
    st.session_state["do_last_call"] = result
    return result


def run_query_auto(message: str) -> Dict[str, Any]:
    # 1) Try DO
    do_res = run_query_via_do(message)
    if do_res.get("ok"):
        return {"source": "DO", "payload": do_res}

    # 2) Fallback
    return {"source": "LOCAL", "payload": {"ok": True, "data": None, "raw_text": "", "error": do_res.get("error")}}


def execute(message: str) -> Dict[str, Any]:
    if backend == "DO knowledge base":
        return {"source": "DO", "payload": run_query_via_do(message)}
    if backend == "Local fallback":
        return {"source": "LOCAL", "payload": {"ok": True, "data": None, "raw_text": ""}}
    return run_query_auto(message)


# -----------------------------
# Quick Actions (generic)
# -----------------------------
QUICK_ACTIONS: List[Tuple[str, str]] = [
    ("📊 Portfolio overview", "Analyze the overall World Bank portfolio performance including disbursement efficiency, sector distribution, regional allocation, and key risks. Return structured metrics if possible."),
    ("🧭 Geographic analysis", "From the World Bank IATI project data, analyze geographic patterns and regional distribution of commitments and disbursements. Provide regional totals and top countries."),
    ("🏷 Sector analysis", "Based on the World Bank IATI project data, analyze commitments by sector and identify the top sectors, growth sectors, and underfunded sectors. Provide totals and percentages."),
    ("📈 Trend analysis", "Conduct a trend analysis of commitments and disbursements over time (at least 5 years). Identify inflection points and explain likely drivers."),
    ("🧯 Risk assessment", "Perform a portfolio risk assessment identifying concentration risks, implementation challenges, disbursement delays, and thematic exposure. Return a risk matrix by region and risk level if possible."),
    ("⚡ Custom action (explain + extract numbers)", "Answer the question, then provide a JSON object with any extracted numeric metrics under keys: totals, by_region, by_sector, trend, risks."),
]


# -----------------------------
# Main layout tabs
# -----------------------------
tab_dashboard, tab_chat, tab_debug = st.tabs(["📊 Dashboard", "💬 Ask / Quick Actions", "🧪 Debug"])

with tab_chat:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Quick Actions")

    cols = st.columns(3)
    for i, (label, prompt) in enumerate(QUICK_ACTIONS):
        with cols[i % 3]:
            if st.button(label, use_container_width=True):
                set_query_text(prompt)

    st.write("")
    st.markdown("#### Ask the agent")

    # Widget key is fixed; we do NOT assign to st.session_state["query_input"] after creation.
    query = st.text_area(
        "Enter your request",
        value=st.session_state["query_text"],
        height=140,
        key="query_input_widget",
        placeholder="E.g., 'Show commitments and disbursements by region for the last 5 years, and highlight bottlenecks.'",
    )

    action_cols = st.columns([1, 1, 3])
    with action_cols[0]:
        run_btn = st.button("Run", type="primary", use_container_width=True)
    with action_cols[1]:
        clear_btn = st.button("Clear", use_container_width=True)

    if clear_btn:
        clear_query()
        st.experimental_rerun()

    if run_btn:
        set_query_text(query)
        with st.spinner("Running query..."):
            t0 = _now_ms()
            res = execute(query)
            t1 = _now_ms()
        st.session_state["last_result"] = {"query": query, "result": res, "ms": (t1 - t0)}

    # Show last result
    if st.session_state["last_result"]:
        lr = st.session_state["last_result"]
        st.write("")
        st.markdown("---")
        st.markdown(f"**Backend used:** `{lr['result']['source']}`  ·  **Time:** `{lr['ms']} ms`")
        payload = lr["result"]["payload"]

        if lr["result"]["source"] == "DO":
            if not payload.get("ok"):
                st.error(f"DO call failed (status={payload.get('status')}): {payload.get('error')}")
                st.caption(f"URL used: {payload.get('url_used')}")
            else:
                # Best-effort: show a clean answer
                data = payload.get("data")
                raw = payload.get("raw_text", "")

                if isinstance(data, dict):
                    # Common response shapes: {"response": "..."} or {"message": "..."} etc.
                    text = (
                        data.get("response")
                        or data.get("answer")
                        or data.get("message")
                        or data.get("output")
                        or None
                    )
                    if isinstance(text, str) and text.strip():
                        st.markdown(text)
                    else:
                        # If dict but no obvious text field, show it
                        st.json(data)
                else:
                    # Fallback to raw text
                    st.markdown(raw if raw else "_(No content returned)_")

        else:
            st.warning(
                "Using local fallback data because DO did not return a usable response. "
                "Fix the DO endpoint route (probe in sidebar) to use real knowledge base data."
            )

    st.markdown("</div>", unsafe_allow_html=True)


with tab_dashboard:
    # For dashboard: attempt to use DO response first; if not, use fallback dataset.
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Executive dashboard")

    st.caption(
        "Charts are generated from real DO knowledge base responses **if structured metrics are returned**; "
        "otherwise a local sample dataset is used as a placeholder."
    )

    # Try to derive structured metrics from last DO call, else fallback
    structured = None
    if st.session_state.get("do_last_call") and st.session_state["do_last_call"].get("ok"):
        data = st.session_state["do_last_call"].get("data")
        raw = st.session_state["do_last_call"].get("raw_text") or ""
        if isinstance(data, dict):
            structured = data.get("metrics") or data.get("data") or extract_json_object(raw)

    # Build dashboard dataset
    dataset = sample_portfolio_data()

    # If you later standardize DO output into a schema, map it here:
    # Example expected schema:
    # structured = {
    #   "regional_investment_by_sector": [{"Category":"Africa","Value":123}, ...],
    #   "active_projects_global": [{"Region":"Africa","ActiveProjects":420,"AvgCommitmentUSDm":85}, ...],
    #   "portfolio_trend": [{"Year":2020,"InvestmentBn":250,"DisbursementBn":190}, ...],
    #   "risk_heatmap": [{"RiskLevel":"Low","Africa":25,...}, ...]
    # }
    if isinstance(structured, dict):
        try:
            if "regional_investment_by_sector" in structured:
                dataset["regional_investment_by_sector"] = pd.DataFrame(structured["regional_investment_by_sector"])
            if "active_projects_global" in structured:
                dataset["active_projects_global"] = pd.DataFrame(structured["active_projects_global"])
            if "portfolio_trend" in structured:
                dataset["portfolio_trend"] = pd.DataFrame(structured["portfolio_trend"])
            if "risk_heatmap" in structured:
                dataset["risk_heatmap"] = pd.DataFrame(structured["risk_heatmap"])
        except Exception:
            # Keep sample fallback if mapping fails
            pass

    # Layout: 2x2
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_bar_regional(dataset["regional_investment_by_sector"]), use_container_width=True)
    with c2:
        st.plotly_chart(fig_bubble_active_projects(dataset["active_projects_global"]), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(fig_line_trend(dataset["portfolio_trend"]), use_container_width=True)
    with c4:
        # Risk heatmap now colorful + legend/colorbar (not “blue all through”)
        st.plotly_chart(fig_risk_heatmap(dataset["risk_heatmap"]), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


with tab_debug:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Debug & Diagnostics")

    st.markdown(
        "- Your logs show **404 on `/chat`** and **404 on `/capabilities`**, plus an earlier **event loop closed** failure. "
        "This UI avoids async loops and includes endpoint probing to locate the correct chat route."
    )

    st.write("")
    st.markdown("**Last DO call**")
    if st.session_state.get("do_last_call"):
        st.json(st.session_state["do_last_call"])
    else:
        st.info("No DO calls yet. Run a query from the Ask tab, or probe endpoints in the sidebar.")

    st.write("")
    st.markdown("**Last app result**")
    if st.session_state.get("last_result"):
        st.json(st.session_state["last_result"])
    else:
        st.info("No app results yet.")

    st.markdown("</div>", unsafe_allow_html=True)
