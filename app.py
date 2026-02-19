import os
import re
import json
import hashlib
import random
from datetime import datetime

import requests
import pandas as pd
import streamlit as st


# ============================================================
# World Bank IATI Intelligence Agent — Dashboard + Chat
# KB-first metrics via formatted text (markdown tables).
# If KB metrics missing, generate labeled DEMO placeholders.
# ============================================================

st.set_page_config(
    page_title="World Bank | IATI Intelligence Agent",
    page_icon="🌍",
    layout="wide",
)

# ---- Secrets / Env (Streamlit Cloud friendly) ----
DO_AGENT_ENDPOINT = st.secrets.get("DO_AGENT_ENDPOINT", os.getenv("DO_AGENT_ENDPOINT", "")).rstrip("/")
DO_AGENT_API_KEY = st.secrets.get("DO_AGENT_API_KEY", os.getenv("DO_AGENT_API_KEY", ""))
AGENT_ID = st.secrets.get("AGENT_ID", os.getenv("AGENT_ID", ""))  # optional / kept for parity

if not DO_AGENT_ENDPOINT:
    st.error("Missing DO_AGENT_ENDPOINT. Add it in Streamlit Secrets or environment variables.")
    st.stop()

# ---- Enterprise gradient styling (teal→cyan→sky, lavender→violet, indigo accents) ----
st.markdown(
    """
    <style>
      :root{
        --bg1:#061a2b;           /* deep blue-teal */
        --bg2:#0b4e7a;           /* ocean */
        --card: rgba(255,255,255,.92);
        --ink:#071a2b;
        --muted:#4b5b6b;

        --teal:#14b8a6;
        --cyan:#22d3ee;
        --sky:#38bdf8;

        --lav:#c4b5fd;
        --violet:#8b5cf6;
        --purple:#a78bfa;

        --indigo:#4f46e5;
        --deep:#1f2a68;
      }

      .stApp {
        background: radial-gradient(1200px 800px at 10% 10%, rgba(34,211,238,.25), transparent 60%),
                    radial-gradient(900px 650px at 85% 25%, rgba(167,139,250,.22), transparent 55%),
                    linear-gradient(135deg, var(--bg1) 0%, var(--bg2) 100%);
      }

      section.main > div{ max-width: 1250px; }

      .wb-header{
        background: var(--card);
        border-radius: 18px;
        padding: 18px 18px;
        box-shadow: 0 14px 38px rgba(0,0,0,.18);
        border: 1px solid rgba(255,255,255,.35);
        backdrop-filter: blur(10px);
        margin-bottom: 14px;
      }
      .wb-title{
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        font-weight: 780;
        letter-spacing: .2px;
        color: var(--ink);
        margin: 0;
        line-height: 1.2;
      }
      .wb-subtitle{
        color: var(--muted);
        margin: 4px 0 0 0;
        font-size: 1.02rem;
      }
      .wb-badge{
        display:inline-flex; align-items:center; gap:8px;
        font-weight:650;
        color:#062a3a;
        background: linear-gradient(90deg, rgba(20,184,166,.18), rgba(56,189,248,.18));
        border: 1px solid rgba(34,211,238,.35);
        padding: 6px 10px;
        border-radius: 999px;
        font-size: .85rem;
      }
      .wb-side{
        background: rgba(255,255,255,.90);
        border: 1px solid rgba(255,255,255,.35);
        border-radius: 16px;
        padding: 14px 14px;
        box-shadow: 0 12px 28px rgba(0,0,0,.14);
      }

      /* KPI cards */
      .kpi{
        background: rgba(255,255,255,.92);
        border: 1px solid rgba(255,255,255,.35);
        border-radius: 16px;
        padding: 14px 14px;
        box-shadow: 0 10px 22px rgba(0,0,0,.12);
      }
      .kpi-label{ color: var(--muted); font-weight: 650; font-size: .86rem; }
      .kpi-value{ color: var(--ink); font-weight: 820; font-size: 1.55rem; margin-top: 4px; }
      .kpi-note{ color: var(--muted); font-size: .82rem; margin-top: 6px; }

      /* Demo data ribbon */
      .demo{
        background: linear-gradient(90deg, rgba(196,181,253,.28), rgba(34,211,238,.18));
        border: 1px solid rgba(79,70,229,.22);
        color: #0b1f3a;
        padding: 10px 12px;
        border-radius: 14px;
        box-shadow: 0 10px 18px rgba(0,0,0,.10);
      }

      /* Chat message card-ish */
      div[data-testid="stChatMessage"]{
        background: rgba(255,255,255,.92);
        border-radius: 16px;
        padding: 10px 12px;
        box-shadow: 0 10px 22px rgba(0,0,0,.12);
        border: 1px solid rgba(255,255,255,.35);
      }
      div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background: linear-gradient(90deg, rgba(34,211,238,.10), rgba(167,139,250,.10));
        border: 1px solid rgba(124,58,237,.18);
      }

      .stChatInput > div{
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,.35) !important;
        box-shadow: 0 12px 26px rgba(0,0,0,.14) !important;
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
          <p class="wb-subtitle">Dashboard + chat insights from the KB (no uploads). Evidence-first. Demo fallback when KB is missing slices.</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Helper: API call (matches your example shape) ----
def call_agent_api(message: str) -> str:
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

    # Standard OpenAI-ish format
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

# ---- Helper: context prefix ----
def build_context(country: str, years: str, sector: str) -> str:
    parts = [f"Country={country}", f"Years={years}"]
    if sector and sector != "All":
        parts.append(f"Sector={sector}")
    return "Context: " + ", ".join(parts)

# ---- Helper: parse markdown table into DataFrame ----
def parse_markdown_table(md: str, header: str) -> pd.DataFrame | None:
    """
    Find a markdown table after a heading like '### KPI' and parse it into a DataFrame.
    Expected:
      ### KPI
      | Metric | Value |
      |---|---|
      | ... | ... |
    """
    # locate section header
    pattern = re.compile(rf"^###\s*{re.escape(header)}\s*$", re.IGNORECASE | re.MULTILINE)
    m = pattern.search(md)
    if not m:
        return None

    # from header onward, capture a table block
    tail = md[m.end():]
    # table block: consecutive lines starting with |
    lines = []
    for line in tail.splitlines():
        line = line.rstrip()
        if line.strip().startswith("|"):
            lines.append(line)
        elif lines:
            break

    if len(lines) < 3:
        return None

    # Basic markdown table parse
    # First row headers, second row separator, then data rows
    header_cells = [c.strip() for c in lines[0].strip("|").split("|")]
    data_rows = []
    for row in lines[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        # pad/truncate
        if len(cells) < len(header_cells):
            cells += [""] * (len(header_cells) - len(cells))
        data_rows.append(cells[: len(header_cells)])

    df = pd.DataFrame(data_rows, columns=header_cells)
    return df

def money_to_float(x: str) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if not s or s.upper() in {"NA", "N/A", "NONE", "NULL", "-"}:
        return None
    # remove currency symbols & commas
    s = re.sub(r"[\$,]", "", s)
    # allow suffixes like M/B
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

# ---- Placeholder generation (deterministic by filters) ----
def seeded_rng(*parts: str) -> random.Random:
    key = "|".join(parts)
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    seed = int(h[:12], 16)
    return random.Random(seed)

def make_demo_data(country: str, years: str, sector: str) -> dict:
    rng = seeded_rng(country, years, sector)
    # plausible totals
    commitments = rng.uniform(0.9, 6.5) * 1e9
    disbursements = commitments * rng.uniform(0.45, 0.88)
    projects = int(rng.uniform(35, 220))
    ratio = (disbursements / commitments) * 100.0

    # timeseries quarterly
    periods = [f"{y} Q{q}" for y in years_range_to_list(years) for q in (1, 2, 3, 4)]
    periods = periods[:12] if len(periods) > 12 else periods
    ts = []
    base_c = commitments / max(len(periods), 1)
    base_d = disbursements / max(len(periods), 1)
    for i, p in enumerate(periods):
        wobble = rng.uniform(0.7, 1.35)
        ts.append({"Period": p, "Commitments": base_c * wobble, "Disbursements": base_d * (wobble * rng.uniform(0.8, 1.05))})

    # sectors
    sector_names = ["Health", "Education", "Energy", "Transport", "Water", "Governance", "Agriculture"]
    rng.shuffle(sector_names)
    weights = [rng.uniform(0.05, 0.25) for _ in range(5)]
    ssum = sum(weights)
    sectors = [{"Sector": sector_names[i], "Value": commitments * (weights[i] / ssum)} for i in range(5)]

    # aid type mix
    mix_names = ["Grants", "Loans", "Technical Assistance", "Equity/Guarantees"]
    mix_weights = [rng.uniform(0.1, 0.5) for _ in mix_names]
    msum = sum(mix_weights)
    mix = [{"Type": mix_names[i], "Value": commitments * (mix_weights[i] / msum)} for i in range(len(mix_names))]

    narrative = (
        f"**DEMO DATA (KB slice missing)**\n\n"
        f"Showing a realistic portfolio pattern for **{country}**, **{years}**"
        + (f", **{sector}**." if sector and sector != "All" else ".")
        + "\n\nUse this dashboard layout to validate UX, then connect the KB slices to replace placeholders."
    )

    return {
        "kpis": {"Commitments": commitments, "Disbursements": disbursements, "Projects": projects, "Disbursement Ratio %": ratio},
        "timeseries": pd.DataFrame(ts),
        "sectors": pd.DataFrame(sectors),
        "mix": pd.DataFrame(mix),
        "narrative": narrative,
    }

def years_range_to_list(years: str) -> list[int]:
    # "2021-2024" -> [2021,2022,2023,2024]
    m = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", years)
    if not m:
        return [datetime.utcnow().year - 3, datetime.utcnow().year - 2, datetime.utcnow().year - 1, datetime.utcnow().year]
    a, b = int(m.group(1)), int(m.group(2))
    if a > b:
        a, b = b, a
    return list(range(a, b + 1))

# ---- Sidebar (filters + quick actions + connection status) ----
with st.sidebar:
    st.markdown("<div class='wb-side'>", unsafe_allow_html=True)
    st.markdown("### Filters")
    country = st.selectbox("Country", ["Global", "KEN", "NGA", "IND", "BRA", "PHL", "IDN", "EGY", "PAK", "ETH"], index=1)
    years = st.selectbox("Year range", ["2020-2023", "2021-2024", "2022-2025"], index=1)
    sector = st.selectbox("Sector", ["All", "Health", "Education", "Energy", "Transport", "Water", "Governance", "Agriculture"], index=0)

    st.divider()
    st.markdown("### Quick Actions")
    PROMPTS = {
        "Refresh dashboard (narrative + tables)":
            "Generate a dashboard narrative and KPI/Chart tables for the current context. "
            "Return formatted markdown only (no JSON).",
        "Executive portfolio brief":
            "Write a 1-page executive brief for the current context. "
            "Include: key trends, what changed, what matters, and 5 evidence items (IATI activity IDs/titles if available).",
        "Effectiveness & results scan":
            "Identify projects with the strongest outcome evidence in the current context. "
            "Summarize patterns and cite evidence (IATI IDs/titles).",
        "Risk & data quality scan":
            "Flag anomalies, missingness, or suspicious patterns in the current context. "
            "Be specific and cite evidence where possible."
    }
    quick = st.selectbox("Insert a standard prompt", ["—"] + list(PROMPTS.keys()))
    if quick != "—":
        st.session_state["draft_prompt"] = PROMPTS[quick]
        st.success("Prompt loaded (you can send it in Chat).")

    st.divider()
    st.markdown("### Connection")
    st.caption(f"Endpoint: `{DO_AGENT_ENDPOINT}`")
    st.caption(f"API key: `{'✅ set' if bool(DO_AGENT_API_KEY) else '❌ missing'}`")
    st.caption(f"Agent ID: `{AGENT_ID or '—'}`")
    st.markdown("</div>", unsafe_allow_html=True)

# ---- Session State ----
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
    st.session_state["dash_md"] = ""  # latest dashboard markdown returned by agent

if "dash_demo" not in st.session_state:
    st.session_state["dash_demo"] = False

# ---- Dashboard prompt spec (formatted text only) ----
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

# ---- Extract metrics from markdown tables; if missing -> DEMO fallback ----
def build_dashboard_from_md(md: str, country: str, years: str, sector: str):
    demo = False

    kpi_df = parse_markdown_table(md, "KPI")
    trend_df = parse_markdown_table(md, "Trend")
    sectors_df = parse_markdown_table(md, "Sectors")
    mix_df = parse_markdown_table(md, "Mix")

    # Heuristic: if any required table missing or contains NA -> fallback demo
    def df_has_na(df: pd.DataFrame | None) -> bool:
        if df is None or df.empty:
            return True
        flat = " ".join(df.astype(str).fillna("").values.flatten().tolist()).upper()
        return "NA" in flat or "N/A" in flat

    if df_has_na(kpi_df) or df_has_na(trend_df) or df_has_na(sectors_df) or df_has_na(mix_df):
        demo = True
        demo_data = make_demo_data(country, years, sector)
        return demo_data, demo

    # Parse KPI
    kpi_map = {}
    for _, row in kpi_df.iterrows():
        metric = str(row.get("Metric", "")).strip()
        val = str(row.get("Value", "")).strip()
        if not metric:
            continue
        if "commit" in metric.lower():
            kpi_map["Commitments"] = money_to_float(val)
        elif "disburs" in metric.lower():
            kpi_map["Disbursements"] = money_to_float(val)
        elif "project" in metric.lower():
            try:
                kpi_map["Projects"] = int(re.sub(r"[^\d]", "", val) or "0")
            except:
                kpi_map["Projects"] = None
        elif "ratio" in metric.lower():
            kpi_map["Disbursement Ratio %"] = pct_to_float(val)

    # Trend
    tdf = trend_df.rename(columns={c: c.strip() for c in trend_df.columns})
    # ensure numeric columns
    if "Commitments" in tdf.columns:
        tdf["Commitments"] = tdf["Commitments"].apply(money_to_float)
    if "Disbursements" in tdf.columns:
        tdf["Disbursements"] = tdf["Disbursements"].apply(money_to_float)

    # Sectors
    sdf = sectors_df.rename(columns={c: c.strip() for c in sectors_df.columns})
    if "Value" in sdf.columns:
        sdf["Value"] = sdf["Value"].apply(money_to_float)

    # Mix
    mdf = mix_df.rename(columns={c: c.strip() for c in mix_df.columns})
    if "Value" in mdf.columns:
        mdf["Value"] = mdf["Value"].apply(money_to_float)

    # Narrative
    narrative = md.split("### KPI")[0].strip() if "### KPI" in md else md

    return {
        "kpis": kpi_map,
        "timeseries": tdf,
        "sectors": sdf,
        "mix": mdf,
        "narrative": narrative,
    }, demo

# ---- Dashboard row ----
top_left, top_right = st.columns([2.1, 1.0], gap="large")

with top_left:
    st.subheader("Portfolio Dashboard")

with top_right:
    refresh = st.button("🔄 Refresh dashboard", type="primary", use_container_width=True)

context = build_context(country, years, sector)

if refresh:
    with st.spinner("Refreshing dashboard from KB…"):
        md = call_agent_api(dashboard_prompt(context))
    st.session_state["dash_md"] = md

# Build dashboard data (KB-first; if missing -> demo)
dash_md = st.session_state.get("dash_md", "")
if dash_md.strip():
    dash_data, is_demo = build_dashboard_from_md(dash_md, country, years, sector)
else:
    # no data yet -> demo so charts render immediately
    dash_data, is_demo = make_demo_data(country, years, sector), True

st.session_state["dash_demo"] = is_demo

# Demo banner
if is_demo:
    st.markdown(
        "<div class='demo'><b>DEMO DATA</b> — The KB did not return enough metrics for this slice. "
        "Charts below are placeholder values generated for UX/demo purposes.</div>",
        unsafe_allow_html=True,
    )

# KPI cards
k = dash_data.get("kpis", {})
kpi_cols = st.columns(4, gap="large")

def fmt_money(v: float | None) -> str:
    if v is None:
        return "—"
    # human readable
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

kpis = [
    ("Total commitments", fmt_money(k.get("Commitments")), "From KB tables or DEMO fallback"),
    ("Total disbursements", fmt_money(k.get("Disbursements")), "From KB tables or DEMO fallback"),
    ("# projects", fmt_int(k.get("Projects")), "Count in scope"),
    ("Disbursement ratio", fmt_pct(k.get("Disbursement Ratio %")), "Disbursements / Commitments"),
]

for i, (label, value, note) in enumerate(kpis):
    with kpi_cols[i]:
        st.markdown(
            f"<div class='kpi'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"<div class='kpi-note'>{note}</div></div>",
            unsafe_allow_html=True,
        )

# Charts layout
c1, c2 = st.columns([1.4, 1.0], gap="large")
c3, c4 = st.columns([1.0, 1.0], gap="large")

ts = dash_data.get("timeseries", pd.DataFrame())
sectors_df = dash_data.get("sectors", pd.DataFrame())
mix_df = dash_data.get("mix", pd.DataFrame())

with c1:
    st.markdown("#### Commitments vs Disbursements (Trend)" + (" — DEMO" if is_demo else ""))
    if not ts.empty and {"Period", "Commitments", "Disbursements"}.issubset(set(ts.columns)):
        chart_df = ts.copy()
        chart_df = chart_df.dropna(subset=["Commitments", "Disbursements"], how="all")
        st.line_chart(chart_df.set_index("Period")[["Commitments", "Disbursements"]])
    else:
        st.info("Trend data not available.")

with c2:
    st.markdown("#### Sector Breakdown" + (" — DEMO" if is_demo else ""))
    if not sectors_df.empty and {"Sector", "Value"}.issubset(set(sectors_df.columns)):
        sdf = sectors_df.dropna(subset=["Value"]).sort_values("Value", ascending=False).head(10)
        st.bar_chart(sdf.set_index("Sector")["Value"])
    else:
        st.info("Sector data not available.")

with c3:
    st.markdown("#### Aid Type / Modality Mix" + (" — DEMO" if is_demo else ""))
    if not mix_df.empty and {"Type", "Value"}.issubset(set(mix_df.columns)):
        mdf = mix_df.dropna(subset=["Value"]).sort_values("Value", ascending=False)
        st.bar_chart(mdf.set_index("Type")["Value"])
    else:
        st.info("Mix data not available.")

with c4:
    st.markdown("#### Dashboard Narrative (Formatted Text)")
    # Show the narrative (formatted markdown), regardless of demo/KB
    st.markdown(dash_data.get("narrative", ""), help=f"{context}")

st.divider()

# ---- Chat ----
st.subheader("Ask the Agent")

# Render history
for m in st.session_state.messages:
    with st.chat_message("assistant" if m["role"] == "assistant" else "user"):
        st.markdown(m["content"])

# Loaded prompt helper (since chat_input can’t be prefilled)
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

# Determine outgoing message
outgoing = None
if send_loaded:
    outgoing = edited
    st.session_state["draft_prompt"] = ""
elif user_input:
    outgoing = user_input

# Send message
if outgoing:
    # Prefix with current filter context (keeps chat aligned with dashboard)
    msg = f"{context}\n\nUser request: {outgoing}"

    st.session_state.messages.append({"role": "user", "content": outgoing})
    with st.chat_message("user"):
        st.markdown(outgoing)

    with st.chat_message("assistant"):
        with st.spinner("Thinking with KB…"):
            reply = call_agent_api(msg)
        # Render formatted text (no JSON)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# Footer
st.caption("© 2026 World Bank — IATI Intelligence Agent (KB-first • demo fallback clearly labeled)")
