# streamlit_app.py
import streamlit as st
import asyncio
from datetime import datetime
import json
import os

# Import orchestrator and config
from wb_iati_agent_config import get_agent_config, AgentConfig
from main_agent_orchestrator import WBIATIAgentOrchestrator

st.set_page_config(page_title="WB IATI Intelligence Agent", layout="wide")

# Load config from env / streamlit secrets
def load_config_from_env() -> AgentConfig:
    cfg = get_agent_config()
    cfg.api_key = os.environ.get("DO_API_KEY", cfg.api_key)
    cfg.endpoint = os.environ.get("DO_ENDPOINT", cfg.endpoint)
    cfg.chatbot_id = os.environ.get("DO_CHATBOT_ID", cfg.chatbot_id)
    return cfg

@st.cache_resource(ttl=3600)
def get_orchestrator():
    cfg = load_config_from_env()
    orchestrator = WBIATIAgentOrchestrator(cfg)
    # initialize synchronously (safe short init)
    try:
        init_ok = asyncio.run(orchestrator.initialize())
    except Exception as e:
        st.error(f"Orchestrator init error: {e}")
        init_ok = False
    orchestrator.is_initialized = init_ok
    return orchestrator

orchestrator = get_orchestrator()

st.title("World Bank — IATI Intelligence Agent")
st.markdown("Ask questions about the World Bank portfolio, create dashboards, or run analytics.")

# status column
col1, col2 = st.columns([3, 1])
with col2:
    st.subheader("Agent Status")
    status = orchestrator.get_agent_status()
    st.write({
        "name": status["agent_info"]["name"],
        "version": status["agent_info"]["version"],
        "initialized": status["agent_info"]["initialized"],
        "endpoint": status["api_config"]["endpoint"]
    })
    if not status["agent_info"]["initialized"]:
        st.warning("Agent not fully initialized. Check logs and secrets.")

with col1:
    st.subheader("Chat / Query")
    query = st.text_area("Enter your natural language query", height=140)
    col_query_btns = st.columns([1,1,1])
    with col_query_btns[0]:
        run_btn = st.button("Run Query")
    with col_query_btns[1]:
        dashboard_btn = st.button("Create Executive Dashboard")
    with col_query_btns[2]:
        clear_btn = st.button("Clear")

    if clear_btn:
        st.experimental_rerun()

    # Handle simple query
    if run_btn and query.strip():
        with st.spinner("Processing query..."):
            try:
                # orchestrator.process_user_query is async — run it
                result = asyncio.run(orchestrator.process_user_query(query))
                if result.get("error"):
                    st.error(result.get("message") or result.get("error"))
                else:
                    st.success("Query processed")
                    st.subheader("Executive summary")
                    st.write(result.get("executive_summary", "No summary"))
                    st.subheader("Key insights")
                    for insight in result.get("key_insights", []):
                        st.markdown(f"**{insight.get('title')}** — {insight.get('finding')}")
                    # raw dump
                    st.expander("Raw response (JSON)", expanded=False).json(result)
            except Exception as e:
                st.error(f"Query processing failed: {e}")

    # Dashboard creation shortcut
    if dashboard_btn:
        with st.spinner("Creating executive dashboard..."):
            try:
                dash = asyncio.run(orchestrator.create_executive_dashboard("executive"))
                if dash.get("error"):
                    st.error(dash.get("error"))
                else:
                    st.success(f"Dashboard created: {dash['title']}")
                    st.download_button("Download Dashboard JSON", dash["configurations"]["json"], file_name=f"{dash['dashboard_id']}.json", mime="application/json")
                    st.write("Preview components:")
                    for c in dash.get("components", 0) and json.loads(dash["configurations"]["json"])["components"]:
                        st.markdown(f"- **{c['title']}** ({c['type']})")
            except Exception as e:
                st.error(f"Dashboard creation failed: {e}")

st.sidebar.header("Quick actions")
if st.sidebar.button("Run Demo Query"):
    st.experimental_rerun()

st.sidebar.markdown("**Environment**")
st.sidebar.write({
    "DO_ENDPOINT": os.environ.get("DO_ENDPOINT"),
    "DO_CHATBOT_ID": os.environ.get("DO_CHATBOT_ID"),
    "DO_API_KEY_set?": bool(os.environ.get("DO_API_KEY"))
})
