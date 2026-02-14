# main_agent_orchestrator.py
"""
World Bank IATI Intelligence Agent - Main Orchestrator
Enterprise-grade orchestration layer for the complete agent system
Streamlit-safe: NO asyncio.run() inside module code paths.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import all agent components
from wb_iati_agent_config import AgentConfig, get_agent_config
from wb_iati_intelligence_agent import WBIATIIntelligenceAgent
from do_api_integration import ChatbotInterface  # compatibility alias points to DigitalOceanAPI
from dashboard_framework import (
    ExecutiveDashboardBuilder, SectorDashboardBuilder,
    CountryDashboardBuilder, ThematicDashboardBuilder,
    DashboardExporter, create_sample_dashboards
)
from advanced_analytics import (
    AdvancedQueryProcessor, TrendAnalyzer,
    AnomalyDetector, InsightGenerator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _safe_get(d: Any, key: str, default=None):
    """Helper to safely read dict-like or object attributes."""
    if d is None:
        return default
    if isinstance(d, dict):
        return d.get(key, default)
    if hasattr(d, "get"):
        try:
            return d.get(key, default)
        except Exception:
            pass
    if hasattr(d, key):
        return getattr(d, key)
    return default


class WBIATIAgentOrchestrator:
    """
    Main orchestrator for the World Bank IATI Intelligence Agent
    Coordinates all components and provides unified interface
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or get_agent_config()

        # Core components
        self.agent = WBIATIIntelligenceAgent(self.config)
        self.chatbot = ChatbotInterface(self.config)  # DigitalOceanAPI-compatible client
        self.analytics = AdvancedQueryProcessor()

        self.is_initialized = False

        # Performance tracking
        self.session_stats = {
            "queries_processed": 0,
            "dashboards_created": 0,
            "insights_generated": 0,
            "avg_response_time": 0.0,
            "session_start": datetime.now()
        }

        logger.info("🚀 WB IATI Intelligence Agent Orchestrator initialized")

    async def initialize(self) -> bool:
        """Initialize all agent components and validate readiness (Streamlit-safe)."""
        logger.info("🔧 Initializing agent components...")

        try:
            # 1) Test API connection (health check)
            logger.info("  1. Testing API connection...")
            health = await self.chatbot.health_check()

            # health may be APIResponse or dict-like; normalize
            ok = _safe_get(health, "success", False)
            if not ok:
                err = _safe_get(health, "error", "Unknown health check error")
                logger.error(f"❌ API connection test failed: {err}")
                return False

            # 2) Optional: fetch capabilities (non-fatal)
            logger.info("  2. Fetching agent capabilities (optional)...")
            try:
                caps = await self.chatbot.get_agent_capabilities()
                if _safe_get(caps, "success", False):
                    logger.info("     ✅ Capabilities available")
                else:
                    logger.warning("     ⚠️ Capabilities not available (continuing)")
            except Exception as e:
                logger.warning(f"     ⚠️ Capabilities check failed (continuing): {e}")

            # 3) Validate dashboard templates (local)
            logger.info("  3. Validating dashboard templates...")
            sample_dashboards = create_sample_dashboards()
            logger.info(f"     ✅ {len(sample_dashboards)} dashboard templates ready")

            # 4) Test analytics pipeline (non-fatal if query parsing is limited)
            logger.info("  4. Testing analytics pipeline...")
            test_query = "What is the World Bank portfolio overview?"
            parsed = self.analytics.parse_complex_query(test_query)

            qt = parsed.get("query_type") if isinstance(parsed, dict) else None
            logger.info(f"     ✅ Query processing validated: {qt or 'ok'}")

            self.is_initialized = True
            logger.info("✅ All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            return False

    async def process_user_query(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        Process user query through the complete intelligence pipeline
        Returns a dict response for Streamlit UI.
        """
        if not self.is_initialized:
            await self.initialize()

        start_time = time.time()
        logger.info(f"🔍 Processing query: '{query[:100]}...'")

        try:
            # Step 1: Parse query using advanced analytics
            parsed_query = self.analytics.parse_complex_query(query)
            query_type = parsed_query.get("query_type", "analysis") if isinstance(parsed_query, dict) else "analysis"
            logger.info(f"  📊 Query type: {query_type}")

            # Step 2: Route to appropriate analysis method
            if query_type == "dashboard_request":
                result = await self._handle_dashboard_request(query, parsed_query, user_context)
            else:
                result = await self._handle_analytical_query(query, parsed_query, user_context)

            # Step 3: Enhance with DO agent if possible
            enhanced_result = await self._enhance_with_do_agent(query, result)

            # Step 4: Generate executive wrapper response
            final_response = self._create_executive_response(query, enhanced_result, parsed_query)

            # Update session statistics
            execution_time = time.time() - start_time
            self._update_session_stats(execution_time)

            logger.info(f"✅ Query processed successfully in {execution_time:.2f}s")
            return final_response

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Query processing failed: {e}", exc_info=True)
            return self._create_error_response(str(e), query, execution_time)

    async def create_executive_dashboard(self, dashboard_type: str, parameters: Dict = None, title: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create executive dashboard with optional remote enrichment."""
        logger.info(f"📊 Creating {dashboard_type} dashboard...")

        try:
            parameters = parameters or {}
            context = context or {}

            # Generate dashboard configuration
            if dashboard_type == "executive":
                dashboard = ExecutiveDashboardBuilder.create_portfolio_overview()
            elif dashboard_type == "sector":
                sector = parameters.get("sector", "Education")
                dashboard = SectorDashboardBuilder.create_sector_analysis(sector)
            elif dashboard_type == "country":
                country = parameters.get("country", "India")
                dashboard = CountryDashboardBuilder.create_country_portfolio(country)
            elif dashboard_type == "climate":
                dashboard = ThematicDashboardBuilder.create_climate_dashboard()
            else:
                raise ValueError(f"Unknown dashboard type: {dashboard_type}")

            if title:
                dashboard.title = title

            # Export to multiple formats
            json_config = DashboardExporter.export_to_json(dashboard)
            powerbi_config = DashboardExporter.export_to_powerbi(dashboard)

            # Optional: ask remote agent to enrich / validate dashboard request
            do_agent_response = None
            try:
                # If your DigitalOcean agent doesn't support dashboard generation endpoints,
                # this will fail gracefully and we’ll still return local configs.
                # The old code called `create_dashboard_request`; we avoid assuming it exists.
                if hasattr(self.chatbot, "send_query"):
                    do_agent_response = await self.chatbot.send_query(
                        f"Create a {dashboard_type} dashboard. Context: {json.dumps(context)[:4000]}",
                        context={"dashboard_type": dashboard_type, "parameters": parameters, "context": context}
                    )
            except Exception as e:
                logger.warning(f"DO agent dashboard enrichment failed (continuing): {e}")

            self.session_stats["dashboards_created"] += 1

            return {
                "dashboard_id": getattr(dashboard, "dashboard_id", f"dash_{int(time.time())}"),
                "title": getattr(dashboard, "title", title or "Dashboard"),
                "components": len(getattr(dashboard, "components", [])),
                "status": "created",
                "configurations": {
                    "json": json_config,
                    "powerbi": powerbi_config
                },
                "do_agent_response": do_agent_response.to_dict() if hasattr(do_agent_response, "to_dict") else (do_agent_response if isinstance(do_agent_response, dict) else None),
                "metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "refresh_interval": getattr(dashboard, "refresh_interval", None),
                    "permissions": getattr(dashboard, "permissions", None)
                }
            }

        except Exception as e:
            logger.error(f"❌ Dashboard creation failed: {e}", exc_info=True)
            return {"error": str(e), "dashboard_type": dashboard_type}

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status and performance metrics."""
        uptime = datetime.now() - self.session_stats["session_start"]

        # Never leak secrets here; UI can mask values if needed.
        endpoint = getattr(self.config, "endpoint", None)
        chatbot_id = getattr(self.config, "chatbot_id", None)

        return {
            "agent_info": {
                "name": getattr(self.config, "agent_name", "World Bank IATI Intelligence Agent"),
                "version": getattr(self.config, "version", "1.0.0"),
                "initialized": self.is_initialized,
                "uptime_seconds": uptime.total_seconds()
            },
            "api_config": {
                "endpoint": endpoint,
                "chatbot_id": chatbot_id,
                "data_coverage": getattr(self.config, "data_coverage", None)
            },
            "session_stats": self.session_stats,
            "capabilities": {
                "query_processing": True,
                "dashboard_creation": True,
                "trend_analysis": True,
                "anomaly_detection": True,
                "executive_insights": True,
                "multi_format_export": True
            },
            "data_sources": getattr(self.config, "data_sources", [])
        }

    async def _handle_analytical_query(self, query: str, parsed_query: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Handle analytical queries through the intelligence agent."""
        agent_result = await self.agent.process_query(query, user_context)

        # Optional stubs for additional analytics methods
        methods = parsed_query.get("intent", {}).get("analytical_methods", []) if isinstance(parsed_query, dict) else []
        if "trend" in methods:
            logger.info("  📈 Trend analysis requested (stub).")
        if "anomaly_detection" in methods:
            logger.info("  🚨 Anomaly detection requested (stub).")

        return agent_result

    async def _handle_dashboard_request(self, query: str, parsed_query: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Handle dashboard creation requests."""
        dashboard_type = "executive"
        parameters: Dict[str, Any] = {}

        entities = parsed_query.get("entities", {}) if isinstance(parsed_query, dict) else {}
        sectors = entities.get("sectors", []) if isinstance(entities, dict) else []
        countries = entities.get("countries", []) if isinstance(entities, dict) else []

        if sectors:
            dashboard_type = "sector"
            parameters["sector"] = sectors[0]
        elif countries:
            dashboard_type = "country"
            parameters["country"] = countries[0]

        return await self.create_executive_dashboard(dashboard_type, parameters)

    async def _enhance_with_do_agent(self, query: str, initial_result: Dict) -> Dict[str, Any]:
        """Enhance results using Digital Ocean agent knowledge (safe, optional)."""
        try:
            context = {
                "initial_analysis": initial_result.get("summary", "") if isinstance(initial_result, dict) else "",
                "data_points": initial_result.get("key_metrics", {}) if isinstance(initial_result, dict) else {},
                "request_type": "enhancement"
            }

            # Use send_query which exists in DigitalOceanAPI replacement
            do_resp = await self.chatbot.send_query(query, context=context)

            if _safe_get(do_resp, "success", False):
                return {
                    **(initial_result if isinstance(initial_result, dict) else {"raw": initial_result}),
                    "do_agent_insights": _safe_get(do_resp, "data", {}),
                    "enhanced": True,
                    "enhancement_metadata": {
                        "status_code": _safe_get(do_resp, "status_code", None),
                        "execution_time": _safe_get(do_resp, "execution_time", None),
                    }
                }

            logger.warning("DO agent enhancement failed, returning original result")
            return {**(initial_result if isinstance(initial_result, dict) else {"raw": initial_result}), "enhanced": False}

        except Exception as e:
            logger.warning(f"DO agent enhancement error: {e}")
            return {**(initial_result if isinstance(initial_result, dict) else {"raw": initial_result}), "enhanced": False, "enhancement_error": str(e)}

    def _create_executive_response(self, query: str, result: Dict, parsed_query: Dict) -> Dict[str, Any]:
        """Create executive-level response with insights and recommendations."""
        return {
            "query": query,
            "response_timestamp": datetime.now().isoformat(),
            "agent_version": getattr(self.config, "version", "1.0.0"),
            "query_classification": parsed_query.get("query_type") if isinstance(parsed_query, dict) else "analysis",
            "confidence": result.get("confidence", 0.85) if isinstance(result, dict) else 0.75,
            "executive_summary": self._generate_executive_summary(result if isinstance(result, dict) else {"raw": result}),
            "detailed_analysis": result,
            "key_insights": self._extract_key_insights(result if isinstance(result, dict) else {"raw": result}),
            "recommendations": self._generate_recommendations(result if isinstance(result, dict) else {"raw": result}),
            "visualization_suggestions": self._suggest_visualizations(parsed_query, result),
            "follow_up_queries": self._suggest_follow_ups(query, result),
            "data_quality": self._assess_data_quality(result),
            "session_context": {
                "query_number": self.session_stats["queries_processed"] + 1,
                "session_duration": (datetime.now() - self.session_stats["session_start"]).total_seconds()
            }
        }

    def _generate_executive_summary(self, result: Dict) -> str:
        """Generate executive-level summary."""
        if result.get("summary"):
            return result["summary"]

        parts: List[str] = []
        if result.get("total_commitment"):
            parts.append(f"Portfolio analysis shows {self._format_currency(result['total_commitment'])} in total commitments")
        if result.get("key_insights"):
            parts.append(f"Generated {len(result['key_insights'])} strategic insights")
        if result.get("enhanced"):
            parts.append("Enhanced with comprehensive knowledge base analysis")

        return " | ".join(parts) if parts else "Analysis completed successfully."

    def _extract_key_insights(self, result: Dict) -> List[Dict[str, Any]]:
        """Extract and format key insights."""
        insights: List[Any] = []

        if isinstance(result.get("key_insights"), list):
            insights.extend(result["key_insights"])

        # DO agent insights (if structured)
        do_insights = result.get("do_agent_insights")
        if isinstance(do_insights, dict) and isinstance(do_insights.get("insights"), list):
            insights.extend(do_insights["insights"])

        formatted: List[Dict[str, Any]] = []
        for insight in insights[:5]:
            if isinstance(insight, dict):
                formatted.append({
                    "title": insight.get("title", "Key Finding"),
                    "impact": insight.get("impact", "Medium"),
                    "finding": insight.get("finding", insight.get("description", "")),
                    "recommendation": insight.get("recommendation", "Continue monitoring"),
                    "confidence": insight.get("confidence", 0.85)
                })
            else:
                formatted.append({
                    "title": "Key Finding",
                    "impact": "Medium",
                    "finding": str(insight),
                    "recommendation": "Continue monitoring",
                    "confidence": 0.75
                })
        return formatted

    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recs = [
            "Continue monitoring key performance indicators.",
            "Review portfolio distribution for optimization opportunities.",
            "Analyze implementation efficiency across sectors."
        ]
        if isinstance(result.get("key_insights"), list):
            for insight in result["key_insights"][:3]:
                if isinstance(insight, dict) and insight.get("recommendation"):
                    recs.append(insight["recommendation"])
        return recs[:5]

    def _update_session_stats(self, execution_time: float):
        """Update session statistics."""
        self.session_stats["queries_processed"] += 1
        count = self.session_stats["queries_processed"]
        prev = self.session_stats["avg_response_time"]
        self.session_stats["avg_response_time"] = ((prev * (count - 1)) + execution_time) / count

    def _create_error_response(self, error: str, query: str, execution_time: float) -> Dict[str, Any]:
        """Create error response."""
        return {
            "error": True,
            "message": error,
            "query": query,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "support_message": "Please contact support with this error information.",
            "suggested_actions": [
                "Try rephrasing your query.",
                "Check that all required secrets are configured.",
                "Verify data availability for the requested scope."
            ]
        }

    def _format_currency(self, amount: float) -> str:
        """Format currency amounts."""
        try:
            amt = float(amount)
        except Exception:
            return str(amount)

        if amt >= 1e9:
            return f"${amt/1e9:.1f}B"
        if amt >= 1e6:
            return f"${amt/1e6:.1f}M"
        return f"${amt:,.0f}"

    # ---- The following are lightweight placeholders to keep UI stable ----
    def _suggest_visualizations(self, parsed_query: Dict, result: Any) -> List[str]:
        return ["Time series chart", "Sector distribution bar chart", "Geographic map"]  # minimal default

    def _suggest_follow_ups(self, query: str, result: Any) -> List[str]:
        return [
            "Break down results by sector.",
            "Show trends over the last 3 years.",
            "Highlight projects with delivery risk."
        ]

    def _assess_data_quality(self, result: Any) -> Dict[str, Any]:
        return {"quality": "unknown", "notes": "Data quality assessment not fully implemented."}


# Command-line interface for local testing only (safe)
async def main():
    print("🌍 World Bank IATI Intelligence Agent")
    print("=" * 50)

    orchestrator = WBIATIAgentOrchestrator()
    init_success = await orchestrator.initialize()

    if not init_success:
        print("❌ Agent initialization failed")
        return

    status = orchestrator.get_agent_status()
    print(f"\n✅ Agent Status: {status['agent_info']['name']} v{status['agent_info']['version']}")
    print(f"🔗 Endpoint: {str(status['api_config']['endpoint'])[:50]}...")

    test_queries = [
        "What is the World Bank's total active portfolio?",
        "Show me education sector trends in Sub-Saharan Africa",
        "Create an executive dashboard for portfolio performance"
    ]

    for i, q in enumerate(test_queries, 1):
        print(f"\n{i}. {q}")
        res = await orchestrator.process_user_query(q)
        if res.get("error"):
            print(f"   ❌ {res.get('message')}")
        else:
            print(f"   ✅ {res.get('executive_summary','')[:120]}...")

    print("\n🎯 Ready.")

if __name__ == "__main__":
    # Only for local CLI runs; Streamlit won't execute this.
    asyncio.run(main())
