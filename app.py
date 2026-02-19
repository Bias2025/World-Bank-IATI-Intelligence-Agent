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
    mix_weigh_
