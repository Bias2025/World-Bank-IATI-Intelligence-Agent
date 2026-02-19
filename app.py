import os
import re
import hashlib
import random
from datetime import datetime

import requests
import pandas as pd
import streamlit as st
import altair as alt


# ============================================================
# World Bank IATI Intelligence Agent — Streamlit (Deployable)
# Dashboard + Chat • KB-first via formatted text (markdown tables)
# DEMO fallback uses HEATMAPS (multi-color + legend)
# Branding: LIGHT background + Teal→Cyan→Sky, Lavender→Violet, Indigo accents
# Narrative panel smaller
# Export: Keep ONLY "Download Last Response (.md)" button
# ============================================================

st.set_page_config(
    page_title="World Bank | IATI Intelligence Agent",
    page_icon="🌍",
    layout="wide",
)

# ---- Secrets / Env (Streamlit Cloud friendly) ----
DO_AGENT_ENDPOINT = st.secrets.get("DO_AGENT_ENDPOINT", os.getenv("DO_AGENT_ENDPOINT", "")).rstrip("/")
DO_AGENT_API_KEY = st.secrets.get("DO_AGENT_API_KEY", os.getenv("DO_AGENT_API_KEY", ""))
AGENT_ID = st.secrets.get("AGENT_ID", os.getenv("AGENT_ID", ""))  # optional / parity

if not DO_AGENT_ENDPOINT:
    st.error("Missing DO_AGENT_ENDPOINT. Add it in Streamlit Secrets or environment variables.")
    st.stop()

# ---- LIGHT enterprise styling (readable) ----
st.markdown(
    """
    <style>
      :root{
        --bgMain:#f4f7fb;
        --card:#ffffff;
        --ink:#0f172a;
        --muted:#64748b;

        --teal:#14b8a6;
        --cyan:#22d3ee;
        --sky:#38bdf8;

        --lav:#c4b5fd;
        --violet:#8b5cf6;
        --indigo:#4f46e5;
      }

      .stApp{
        background: linear-gradient(180deg, #f8fbff 0%, #eef3f9 100%);
      }

      section.main > div{ max-width: 1250px; }

      .wb-header{
        background: var(--card);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 12px 30px rgba(0,0,0,.06);
        border: 1px solid rgba(0,0,0,.04);
        margin-bottom: 18px;
      }

      .wb-title{
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        font-weight: 820;
        letter-spacing: .2px;
        color: var(--ink);
        margin: 0;
        line-height: 1.2;
      }

      .wb-subtitle{
        color: var(--muted);
        margin: 6px 0 0 0;
        font-size: 1.00rem;
      }

      .wb-badge{
        display:inline-flex; align-items:center; gap:8px;
        font-weight:750;
        color: #0b2233;
        background: linear-gradient(90deg, rgba(20,184,166,.14), rgba(56,189,248,.14));
        border: 1px solid rgba(34,211,238,.28);
        padding: 6px 10px;
        border-radius: 999px;
        font-size: .85rem;
      }

      .wb-side{
        background: var(--card);
        border: 1px solid rgba(0,0,0,.05);
        border-radius: 16px;
        padding: 14px 14px;
        box-shadow: 0 10px 24px rgba(0,0,0,.05);
      }

      .kpi{
        background: var(--card);
        border-radius: 14px;
        padding: 16px;
        border: 1px solid rgba(0,0,0,.05);
        box-shadow: 0 6px 18px rgba(0,0,0,.05);
      }

      .kpi-label{ color: var(--muted); font-weight: 700; font-size: .86rem; }
      .kpi-value{ color: var(--ink); font-weight: 850; font-size: 1.55rem; margin-top: 4px; }
      .kpi-note{ color: var(--muted); font-size: .82rem; margin-top: 6px; }

      .demo{
        background: linear-gradient(90deg, rgba(196,181,253,.18), rgba(34,211,238,.12));
        border-radius: 14px;
        padding: 12px;
        border: 1px solid rgba(139,92,246,.20);
        color: #0f172a;
        box-shadow: 0 6px 16px rgba(0,0,0,.05);
      }

      .narrative-small{
        font-size: 0.88rem;
        color: #334155;
      }

      /* Primary button: teal→sky */
      div.stButton > button[kind="primary"]{
        background: linear-gradient(90deg, var(--teal), var(--sky)) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 10px 22px rgba(34,211,238,.18) !important;
        font-weight: 780 !important;
      }
      div.stButton > button[kind="primary"]:hover{
        transform: translateY(-1px);
        filter: brightness(1.02);
      }

      /* Chat bubbles (keep light) */
      div[data-testid="stChatMessage"]{
        background: var(--card);
        border-radius: 16px;
        padding: 10px 12px;
        box-shadow: 0 8px 18px rgba(0,0,0,.05);
        border: 1px solid rgba(0,0,0,.05);
      }
      div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background: linear-gradient(90deg, rgba(34,211,238,.10), rgba(196,181,253,.10));
        border: 1px solid rgba(79,70,229,.14);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Header ----
st.markdown(
    """
    <div class="wb-header">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <div class="wb-badge">🌍 World Bank • IATI Intelligence</div>
        <div>
          <h1 class="wb-title">World Bank IATI Intelligence Agent</h1>
          <p class="wb-subtitle">DTransforming IATI data into development intelligence anyone can use.</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Helpers
# ============================================================

def call_agent_api(message: str) -> str:
    """Calls DO agent endpoint and returns formatted text."""
    if not DO_AGENT_API_KEY:
        return "Missing DO_AGENT_API_KEY. Add it in Streamlit Secrets to enable backend calls."

    url = f"{DO_AGENT_ENDPOINT}/api/v1/chat/completions"
    payload = {
        "messages": [{"role": "user", "content": message}],
        "stream": False,
        "include_functions_info": True,
        "include_retrieval_info": True,
        "include_guardrails_info": True,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DO_AGENT_API_KEY}"}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=80)
    except Exception as e:
        return f"Network error calling agent endpoint: {e}"

    if not r.ok:
        return f"API error: {r.status_code} {r.reason}\n\n{r.text[:1500]}"

    data = r.json()

    if isinstance(data, dict) and data.get("choices"):
        msg = data["choices"][0].get("message", {}) or {}
        if msg.get("content"):
            return msg["content"]
        if msg.get("reasoning_content"):
            return msg["reasoning_content"]

    for k in ("message", "content", "response"):
        if isinstance(data, dict) and data.get(k):
            return str(data[k])

    return "Received a response, but couldn’t recognize the payload format."

def build_context(country: str, years: str, sector: str) -> str:
    parts = [f"Country={country}", f"Years={years}"]
    if sector and sector != "All":
        parts.append(f"Sector={sector}")
    return "Context: " + ", ".join(parts)

def parse_markdown_table(md: str, header: str) -> pd.DataFrame | None:
    pattern = re.compile(rf"^###\s*{re.escape(header)}\s*$", re.IGNORECASE | re.MULTILINE)
    m = pattern.search(md)
    if not m:
        return None

    tail = md[m.end():]
    lines = []
    for line in tail.splitlines():
        line = line.rstrip()
        if line.strip().startswith("|"):
            lines.append(line)
        elif lines:
            break

    if len(lines) < 3:
        return None

    header_cells = [c.strip() for c in lines[0].strip("|").split("|")]
    data_rows = []
    for row in lines[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < len(header_cells):
            cells += [""] * (len(header_cells) - len(cells))
        data_rows.append(cells[: len(header_cells)])

    return pd.DataFrame(data_rows, columns=header_cells)

def money_to_float(x: str) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if not s or s.upper() in {"NA", "N/A", "NONE", "NULL", "-"}:
        return None
    s = re.sub(r"[\$,]", "", s)
    mult = 1.0
    if re.search(r"[bB]\b", s):
        mult = 1e9
        s = re.sub(r"[bB]\b", "", s).strip()
    elif re.search(r"[mM]\b", s):
        mult = 1e6
        s = re.sub(r"[mM]\b", "", s).strip()
    try:
        return float(s) * mult
    except:
        return None

def pct_to_float(x: str) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if not s or s.upper() in {"NA", "N/A", "NONE", "NULL", "-"}:
        return None
    s = s.replace("%", "").strip()
    try:
        return float(s)
    except:
        return None

def years_range_to_list(years: str) -> list[int]:
    m = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", years)
    if not m:
        y = datetime.utcnow().year
        return [y - 3, y - 2, y - 1, y]
    a, b = int(m.group(1)), int(m.group(2))
    if a > b:
        a, b = b, a
    return list(range(a, b + 1))

def seeded_rng(*parts: str) -> random.Random:
    key = "|".join(parts)
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    seed = int(h[:12], 16)
    return random.Random(seed)

# ---- DEMO data (KPIs + heatmaps) ----
def make_demo_kpis(country: str, years: str, sector: str) -> dict:
    rng = seeded_rng(country, years, sector)
    commitments = rng.uniform(0.9, 6.5) * 1e9
    disbursements = commitments * rng.uniform(0.45, 0.88)
    projects = int(rng.uniform(35, 220))
    ratio = (disbursements / commitments) * 100.0
    return {
        "Commitments": commitments,
        "Disbursements": disbursements,
        "Projects": projects,
        "Disbursement Ratio %": ratio,
    }

def make_demo_heatmap_df(country: str, years: str, sector: str) -> pd.DataFrame:
    rng = seeded_rng(country, years, sector)
    periods = [f"{y} Q{q}" for y in years_range_to_list(years) for q in (1, 2, 3, 4)]
    periods = periods[:12] if len(periods) > 12 else periods

    sector_names = ["Health", "Education", "Energy", "Transport", "Water", "Governance", "Agriculture"]
    if sector and sector != "All" and sector in sector_names:
        sector_names = [sector] + [s for s in sector_names if s != sector]
    sector_names = sector_names[:6]

    rows = []
    base = rng.uniform(40, 140)
    for s in sector_names:
        s_bias = rng.uniform(0.8, 1.4)
        for i, p in enumerate(periods):
            trend = 1.0 + (i / max(len(periods) - 1, 1)) * rng.uniform(0.05, 0.25)
            noise = rng.uniform(0.75, 1.35)
            val = base * s_bias * trend * noise
            rows.append({"Row": s, "Column": p, "Intensity": val})
    return pd.DataFrame(rows)

def make_demo_type_heatmap_df(country: str, years: str, sector: str) -> pd.DataFrame:
    rng = seeded_rng(country, years, sector, "mix")
    periods = [f"{y} Q{q}" for y in years_range_to_list(years) for q in (1, 2, 3, 4)]
    periods = periods[:12] if len(periods) > 12 else periods
    types = ["Grants", "Loans", "Technical Assistance", "Equity/Guarantees"]
    rows = []
    for t in types:
        bias = rng.uniform(0.7, 1.5)
        for i, p in enumerate(periods):
            val = rng.uniform(20, 120) * bias * (1.0 + i * 0.03) * rng.uniform(0.7, 1.25)
            rows.append({"Row": t, "Column": p, "Intensity": val})
    return pd.DataFrame(rows)

def render_heatmap(df: pd.DataFrame, title: str, row_title: str):
    ramp = ["#0f172a", "#14b8a6", "#22d3ee", "#38bdf8", "#c4b5fd", "#8b5cf6"]
    chart = (
        alt.Chart(df)
        .mark_rect(cornerRadius=3)
        .encode(
            x=alt.X("Column:N", title=None, axis=alt.Axis(labelAngle=90)),
            y=alt.Y("Row:N", title=row_title),
            color=alt.Color(
                "Intensity:Q",
                title="Intensity",
                scale=alt.Scale(range=ramp),
                legend=alt.Legend(orient="right"),
            ),
            tooltip=[
                alt.Tooltip("Row:N", title=row_title),
                alt.Tooltip("Column:N", title="Period"),
                alt.Tooltip("Intensity:Q", format=".1f"),
            ],
        )
        .properties(height=320, title=title)
    )
    st.altair_chart(chart, use_container_width=True)

# ---- KB dashboard prompt spec (formatted markdown only; tables for charts) ----
def dashboard_prompt(context: str) -> str:
    return f"""
You are the World Bank IATI Intelligence Agent.

{context}

Return **formatted markdown only** (no JSON) in this exact structure:

## Dashboard Narrative
(5–10 bullets, executive-friendly. Mention time window and scope.)

### KPI
| Metric | Value |
|---|---|
| Total commitments | <number USD> |
| Total disbursements | <number USD> |
| # projects | <integer> |
| Disbursement ratio | <percent> |

### Trend
| Period | Commitments | Disbursements |
|---|---:|---:|
| 2023 Q1 | ... | ... |

### Sectors
| Sector | Value |
|---|---:|
| Health | ... |

### Mix
| Type | Value |
|---|---:|
| Grants | ... |

### Evidence
(Up to 6 items. Prefer IATI activity identifiers + short titles. If unavailable, say so clearly.)

If the KB does not contain enough data to fill tables, explicitly write 'NA' in the Value cells.
"""

def build_dashboard_from_md(md: str):
    kpi_df = parse_markdown_table(md, "KPI")
    trend_df = parse_markdown_table(md, "Trend")
    sectors_df = parse_markdown_table(md, "Sectors")
    mix_df = parse_markdown_table(md, "Mix")

    def df_has_na(df: pd.DataFrame | None) -> bool:
        if df is None or df.empty:
            return True
        flat = " ".join(df.astype(str).fillna("").values.flatten().tolist()).upper()
        return "NA" in flat or "N/A" in flat

    missing = df_has_na(kpi_df) or df_has_na(trend_df) or df_has_na(sectors_df) or df_has_na(mix_df)
    if missing:
        return None

    kpi_map = {}
    for _, row in kpi_df.iterrows():
        metric = str(row.get("Metric", "")).strip()
        val = str(row.get("Value", "")).strip()
        ml = metric.lower()
        if "commit" in ml:
            kpi_map["Commitments"] = money_to_float(val)
        elif "disburs" in ml:
            kpi_map["Disbursements"] = money_to_float(val)
        elif "project" in ml:
            try:
                kpi_map["Projects"] = int(re.sub(r"[^\d]", "", val) or "0")
            except:
                kpi_map["Projects"] = None
        elif "ratio" in ml:
            kpi_map["Disbursement Ratio %"] = pct_to_float(val)

    tdf = trend_df.rename(columns={c: c.strip() for c in trend_df.columns})
    if "Commitments" in tdf.columns:
        tdf["Commitments"] = tdf["Commitments"].apply(money_to_float)
    if "Disbursements" in tdf.columns:
        tdf["Disbursements"] = tdf["Disbursements"].apply(money_to_float)

    sdf = sectors_df.rename(columns={c: c.strip() for c in sectors_df.columns})
    if "Value" in sdf.columns:
        sdf["Value"] = sdf["Value"].apply(money_to_float)

    mdf = mix_df.rename(columns={c: c.strip() for c in mix_df.columns})
    if "Value" in mdf.columns:
        mdf["Value"] = mdf["Value"].apply(money_to_float)

    narrative = md.split("### KPI")[0].strip() if "### KPI" in md else md
    return {"kpis": kpi_map, "trend": tdf, "sectors": sdf, "mix": mdf, "narrative": narrative}

def fmt_money(v: float | None) -> str:
    if v is None:
        return "—"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

def fmt_int(v) -> str:
    try:
        return f"{int(v):,}"
    except:
        return "—"

def fmt_pct(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:.1f}%"

# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown("<div class='wb-side'>", unsafe_allow_html=True)
    st.markdown("### Filters")
    country = st.selectbox("Country", ["Global", "KEN", "NGA", "IND", "BRA", "PHL", "IDN", "EGY", "PAK", "ETH"], index=1)
    years = st.selectbox("Year range", ["2020-2023", "2021-2024", "2022-2025"], index=1)
    sector = st.selectbox("Sector", ["All", "Health", "Education", "Energy", "Transport", "Water", "Governance", "Agriculture"], index=0)

    st.divider()
    st.markdown("### Quick Actions (KB-aware)")
    PROMPTS = {
        "Refresh dashboard (narrative + tables)": (
            "Generate a dashboard narrative and KPI/Chart tables for the current context. "
            "Return formatted markdown only (no JSON)."
        ),
        "Transaction flow diagnostics (commit vs disburse)": (
            "Analyze commitment vs disbursement transactions for the current context. "
            "Identify lag patterns between commitment dates and disbursement dates, and flag anomalies. "
            "Cite IATI activity identifiers."
        ),
        "Sector concentration & diversification": (
            "Assess sector concentration in the selected portfolio. "
            "Identify over-reliance on specific sectors and summarize diversification opportunities. "
            "Cite sector codes/names and IATI activity identifiers where possible."
        ),
        "Results & indicator performance scan": (
            "Identify projects with results frameworks and measurable indicators in the current context. "
            "Summarize outcome trends and note missing or weak indicator data. "
            "Cite IATI activity IDs and result titles."
        ),
        "Donor / implementing partner network map": (
            "Analyze participating organizations in the selected portfolio. "
            "Identify top donors and implementing agencies, and highlight duplication/coordination gaps. "
            "Cite organization identifiers and linked activities."
        ),
    }
    quick = st.selectbox("Insert a standard prompt", ["—"] + list(PROMPTS.keys()))
    if quick != "—":
        st.session_state["draft_prompt"] = PROMPTS[quick]
        st.success("Prompt loaded (send it in Chat).")

    st.divider()
    st.markdown("### Connection")
    st.caption(f"Endpoint: `{DO_AGENT_ENDPOINT}`")
    st.caption(f"API key: `{'✅ set' if bool(DO_AGENT_API_KEY) else '❌ missing'}`")
    st.caption(f"Agent ID: `{AGENT_ID or '—'}`")
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# Session State
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi — I’m the **World Bank IATI Intelligence Agent**.\n\n"
                "Use the dashboard to explore the portfolio, then ask questions in chat.\n"
                "I’ll cite evidence when available in the KB.\n\n"
                "Tip: Click **Refresh dashboard** to pull KPI + chart data for your selected filters."
            ),
        }
    ]
if "draft_prompt" not in st.session_state:
    st.session_state["draft_prompt"] = ""
if "dash_md" not in st.session_state:
    st.session_state["dash_md"] = ""
if "last_response" not in st.session_state:
    st.session_state["last_response"] = ""

# ============================================================
# Dashboard
# ============================================================

context = build_context(country, years, sector)

top_left, top_right = st.columns([2.1, 1.0], gap="large")
with top_left:
    st.subheader("Portfolio Dashboard")
with top_right:
    refresh = st.button("🔄 Refresh dashboard", type="primary", use_container_width=True)

if refresh:
    with st.spinner("Refreshing dashboard from KB…"):
        md = call_agent_api(dashboard_prompt(context))
    st.session_state["dash_md"] = md

dash_md = st.session_state.get("dash_md", "").strip()
kb_parsed = build_dashboard_from_md(dash_md) if dash_md else None
is_demo = kb_parsed is None

if is_demo:
    kpis_map = make_demo_kpis(country, years, sector)
    narrative = (
        f"**DEMO DATA (KB slice missing)**\n\n"
        f"- Scope: **{country}**, **{years}**"
        + (f", **{sector}**" if sector and sector != "All" else "")
        + "\n- Metrics + heatmaps are placeholder values generated to validate UX.\n"
        "- Once the KB returns KPI/Trend/Sectors/Mix tables, the dashboard will auto-switch to KB data."
    )
else:
    kpis_map = kb_parsed["kpis"]
    narrative = kb_parsed["narrative"]

if is_demo:
    st.markdown(
        "<div class='demo'><b>DEMO DATA</b> — KB did not return enough metrics for this slice. "
        "Heatmaps below are placeholder values generated for UX/demo purposes (with legend).</div>",
        unsafe_allow_html=True,
    )

# KPI cards
kpi_cols = st.columns(4, gap="large")
kpis = [
    ("Total commitments", fmt_money(kpis_map.get("Commitments")), "From KB tables or DEMO fallback"),
    ("Total disbursements", fmt_money(kpis_map.get("Disbursements")), "From KB tables or DEMO fallback"),
    ("# projects", fmt_int(kpis_map.get("Projects")), "Count in scope"),
    ("Disbursement ratio", fmt_pct(kpis_map.get("Disbursement Ratio %")), "Disbursements / Commitments"),
]
for i, (label, value, note) in enumerate(kpis):
    with kpi_cols[i]:
        st.markdown(
            f"<div class='kpi'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"<div class='kpi-note'>{note}</div></div>",
            unsafe_allow_html=True,
        )

# Charts + Narrative
c1, c2 = st.columns([1.4, 1.0], gap="large")
c3, c4 = st.columns([1.0, 1.0], gap="large")

with c1:
    if is_demo:
        st.markdown("#### Portfolio Heatmap — DEMO")
        hdf = make_demo_heatmap_df(country, years, sector)
        render_heatmap(hdf, "Disbursement Intensity by Sector × Period — DEMO", row_title="Sector")
    else:
        st.markdown("#### Commitments vs Disbursements (Trend)")
        ts = kb_parsed["trend"]
        if not ts.empty and {"Period", "Commitments", "Disbursements"}.issubset(set(ts.columns)):
            chart_df = ts.copy().dropna(subset=["Commitments", "Disbursements"], how="all")
            st.line_chart(chart_df.set_index("Period")[["Commitments", "Disbursements"]])
        else:
            st.info("Trend data not available.")

with c2:
    if is_demo:
        st.markdown("#### Sector Heatmap — DEMO")
        hdf = make_demo_heatmap_df(country, years, sector)
        render_heatmap(hdf, "Sector Activity Intensity — DEMO", row_title="Sector")
    else:
        st.markdown("#### Sector Breakdown")
        sdf = kb_parsed["sectors"]
        if not sdf.empty and {"Sector", "Value"}.issubset(set(sdf.columns)):
            sdf2 = sdf.dropna(subset=["Value"]).sort_values("Value", ascending=False).head(10)
            st.bar_chart(sdf2.set_index("Sector")["Value"])
        else:
            st.info("Sector data not available.")

with c3:
    if is_demo:
        st.markdown("#### Modality Heatmap — DEMO")
        mhd = make_demo_type_heatmap_df(country, years, sector)
        render_heatmap(mhd, "Modality Intensity by Type × Period — DEMO", row_title="Type")
    else:
        st.markdown("#### Aid Type / Modality Mix")
        mdf = kb_parsed["mix"]
        if not mdf.empty and {"Type", "Value"}.issubset(set(mdf.columns)):
            mdf2 = mdf.dropna(subset=["Value"]).sort_values("Value", ascending=False)
            st.bar_chart(mdf2.set_index("Type")["Value"])
        else:
            st.info("Mix data not available.")

with c4:
    st.markdown("#### Dashboard Narrative (Formatted Text)")
    st.markdown(f"<div class='narrative-small'>{narrative}</div>", unsafe_allow_html=True)
    st.caption(context)

st.divider()

# ============================================================
# Chat
# ============================================================

st.subheader("Ask the Agent")

for m in st.session_state.messages:
    with st.chat_message("assistant" if m["role"] == "assistant" else "user"):
        st.markdown(m["content"])

default_text = st.session_state.get("draft_prompt", "")
if default_text:
    st.info("A standard prompt is loaded. Click **Send loaded prompt** or edit it below.")
    edited = st.text_area("Loaded prompt (editable):", value=default_text, height=120)
    col_a, col_b = st.columns([1, 1])
    with col_a:
        send_loaded = st.button("Send loaded prompt", type="primary")
    with col_b:
        clear_loaded = st.button("Clear loaded prompt")
    if clear_loaded:
        st.session_state["draft_prompt"] = ""
        st.rerun()
else:
    send_loaded = False
    edited = ""

user_input = st.chat_input("Ask about aid flows, project effectiveness, sectors, outcomes…")

outgoing = None
if send_loaded:
    outgoing = edited
    st.session_state["draft_prompt"] = ""
elif user_input:
    outgoing = user_input

if outgoing:
    msg = f"{context}\n\nUser request: {outgoing}"

    st.session_state.messages.append({"role": "user", "content": outgoing})
    with st.chat_message("user"):
        st.markdown(outgoing)

    with st.chat_message("assistant"):
        with st.spinner("Thinking with KB…"):
            reply = call_agent_api(msg)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state["last_response"] = reply

# Export last chat response: KEEP download button ONLY
st.markdown("### Export Last Chat Response")
st.download_button(
    label="Download Last Response (.md)",
    data=(st.session_state.get("last_response") or ""),
    file_name="agent_response.md",
    mime="text/markdown",
    use_container_width=True,
)

st.caption("© 2026 World Bank — IATI Intelligence Agent (KB-first • DEMO heatmap fallback clearly labeled)")
