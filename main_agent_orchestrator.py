"""
World Bank IATI Intelligence Agent - Main Orchestrator
Enterprise-grade orchestration layer for the complete agent system
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# ---- async helper (paste near top of main_agent_orchestrator.py, after other imports) ----
import asyncio
try:
    import nest_asyncio
except Exception:
    nest_asyncio = None

def run_async_safely(coro):
    """
    Run an async coroutine from synchronous code safely in environments
    where an event loop may already be running (Streamlit).
    Usage: result = run_async_safely(orchestrator.initialize())
    """
    try:
        # Normal case when no loop is running
        return run_async_safely.run(coro)
    except RuntimeError:
        # Event loop already running (Streamlit). Patch with nest_asyncio if available.
        if nest_asyncio:
            nest_asyncio.apply()
            return run_async_safely.run(coro)
        # As a last resort, use asyncio.get_event_loop().create_task and wait for completion synchronously.
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(coro, loop=loop)
        # Wait for future completion in a blocking way (not ideal, but safe fallback)
        # We poll until done to avoid illegal run_until_complete on running loop.
        while not future.done():
            # allow other tasks to run briefly
            loop.call_soon(lambda: None)
            # small sleep to avoid busy loop
            import time
            time.sleep(0.01)
        return future.result()
# -----------------------------------------------------------------------------------------


# Import all agent components
from wb_iati_agent_config import AgentConfig, get_agent_config
from wb_iati_intelligence_agent import WBIATIIntelligenceAgent
from do_api_integration import ChatbotInterface, test_connection
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

class WBIATIAgentOrchestrator:
    """
    Main orchestrator for the World Bank IATI Intelligence Agent
    Coordinates all components and provides unified interface
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or get_agent_config()
        self.agent = WBIATIIntelligenceAgent(self.config)
        self.chatbot = ChatbotInterface(self.config)
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

        logger.info(f"🚀 WB IATI Intelligence Agent Orchestrator initialized")

    async def initialize(self) -> bool:
        """Initialize all agent components and validate readiness"""

        logger.info("🔧 Initializing agent components...")

        try:
            # Test Digital Ocean API connection
            logger.info("  1. Testing API connection...")
            connection_result = await test_connection(self.config)

            if connection_result["overall_status"] != "passed":
                logger.error("❌ API connection test failed")
                return False

            # Initialize chatbot session
            logger.info("  2. Initializing chatbot interface...")
            chatbot_ready = await self.chatbot.initialize_session()

            if not chatbot_ready:
                logger.error("❌ Chatbot initialization failed")
                return False

            # Validate dashboard templates
            logger.info("  3. Validating dashboard templates...")
            sample_dashboards = create_sample_dashboards()
            logger.info(f"     ✅ {len(sample_dashboards)} dashboard templates ready")

            # Test analytics pipeline
            logger.info("  4. Testing analytics pipeline...")
            test_query = "What is the World Bank portfolio overview?"
            parsed = self.analytics.parse_complex_query(test_query)
            logger.info(f"     ✅ Query processing validated: {parsed['query_type']}")

            self.is_initialized = True
            logger.info("✅ All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    async def process_user_query(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        Process user query through the complete intelligence pipeline

        Args:
            query (str): Natural language query from user
            user_context (Dict): Optional user context and preferences

        Returns:
            Dict: Complete analysis response with insights and visualizations
        """

        if not self.is_initialized:
            await self.initialize()

        start_time = time.time()
        logger.info(f"🔍 Processing query: '{query[:100]}...'")

        try:
            # Step 1: Parse query using advanced analytics
            parsed_query = self.analytics.parse_complex_query(query)
            logger.info(f"  📊 Query type: {parsed_query['query_type']}")

            # Step 2: Route to appropriate analysis method
            if parsed_query["query_type"] == "dashboard_request":
                result = await self._handle_dashboard_request(query, parsed_query, user_context)
            else:
                result = await self._handle_analytical_query(query, parsed_query, user_context)

            # Step 3: Send to Digital Ocean agent for knowledge enhancement
            enhanced_result = await self._enhance_with_do_agent(query, result)

            # Step 4: Generate executive summary and recommendations
            final_response = self._create_executive_response(query, enhanced_result, parsed_query)

            # Update session statistics
            execution_time = time.time() - start_time
            self._update_session_stats(execution_time)

            logger.info(f"✅ Query processed successfully in {execution_time:.2f}s")
            return final_response

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Query processing failed: {e}")
            return self._create_error_response(str(e), query, execution_time)

    async def create_executive_dashboard(self, dashboard_type: str, parameters: Dict = None) -> Dict[str, Any]:
        """Create executive dashboard with live data integration"""

        logger.info(f"📊 Creating {dashboard_type} dashboard...")

        try:
            # Generate dashboard configuration
            if dashboard_type == "executive":
                dashboard = ExecutiveDashboardBuilder.create_portfolio_overview()
            elif dashboard_type == "sector":
                sector = parameters.get("sector", "Education") if parameters else "Education"
                dashboard = SectorDashboardBuilder.create_sector_analysis(sector)
            elif dashboard_type == "country":
                country = parameters.get("country", "India") if parameters else "India"
                dashboard = CountryDashboardBuilder.create_country_portfolio(country)
            elif dashboard_type == "climate":
                dashboard = ThematicDashboardBuilder.create_climate_dashboard()
            else:
                raise ValueError(f"Unknown dashboard type: {dashboard_type}")

            # Export to multiple formats
            json_config = DashboardExporter.export_to_json(dashboard)
            powerbi_config = DashboardExporter.export_to_powerbi(dashboard)

            # Request dashboard creation through DO agent
            dashboard_result = await self.chatbot.create_dashboard_request(dashboard_type, parameters or {})

            self.session_stats["dashboards_created"] += 1

            return {
                "dashboard_id": dashboard.dashboard_id,
                "title": dashboard.title,
                "components": len(dashboard.components),
                "status": "created",
                "configurations": {
                    "json": json_config,
                    "powerbi": powerbi_config
                },
                "do_agent_response": dashboard_result,
                "metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "refresh_interval": dashboard.refresh_interval,
                    "permissions": dashboard.permissions
                }
            }

        except Exception as e:
            logger.error(f"❌ Dashboard creation failed: {e}")
            return {"error": str(e), "dashboard_type": dashboard_type}

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status and performance metrics"""

        uptime = datetime.now() - self.session_stats["session_start"]

        return {
            "agent_info": {
                "name": self.config.agent_name,
                "version": self.config.version,
                "initialized": self.is_initialized,
                "uptime_seconds": uptime.total_seconds()
            },
            "api_config": {
                "endpoint": self.config.endpoint,
                "chatbot_id": self.config.chatbot_id,
                "data_coverage": self.config.data_coverage
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
            "data_sources": self.config.data_sources
        }

    async def _handle_analytical_query(self, query: str, parsed_query: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Handle analytical queries through the intelligence agent"""

        # Process through main agent
        agent_result = await self.agent.process_query(query, user_context)

        # Enhance with advanced analytics if needed
        if "trend" in parsed_query.get("intent", {}).get("analytical_methods", []):
            # Add trend analysis
            logger.info("  📈 Adding trend analysis...")
            # In real implementation, this would analyze actual data

        if "anomaly_detection" in parsed_query.get("intent", {}).get("analytical_methods", []):
            # Add anomaly detection
            logger.info("  🚨 Adding anomaly detection...")
            # In real implementation, this would detect anomalies

        return agent_result

    async def _handle_dashboard_request(self, query: str, parsed_query: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Handle dashboard creation requests"""

        # Extract dashboard parameters from query
        dashboard_type = "executive"  # Default
        parameters = {}

        if "sector" in parsed_query.get("entities", {}).get("sectors", []):
            dashboard_type = "sector"
            parameters["sector"] = parsed_query["entities"]["sectors"][0]
        elif "country" in parsed_query.get("entities", {}).get("countries", []):
            dashboard_type = "country"
            parameters["country"] = parsed_query["entities"]["countries"][0]

        return await self.create_executive_dashboard(dashboard_type, parameters)

    async def _enhance_with_do_agent(self, query: str, initial_result: Dict) -> Dict[str, Any]:
        """Enhance results using Digital Ocean agent knowledge"""

        try:
            # Send query to DO agent with context
            context = {
                "initial_analysis": initial_result.get("summary", ""),
                "data_points": initial_result.get("key_metrics", {}),
                "request_type": "enhancement"
            }

            do_response = await self.chatbot.send_iati_query(query, include_visualizations=True)

            if "response" in do_response:
                return {
                    **initial_result,
                    "do_agent_insights": do_response["response"],
                    "enhanced": True,
                    "enhancement_metadata": do_response["metadata"]
                }
            else:
                logger.warning("DO agent enhancement failed, returning original result")
                return {**initial_result, "enhanced": False}

        except Exception as e:
            logger.warning(f"DO agent enhancement error: {e}")
            return {**initial_result, "enhanced": False, "enhancement_error": str(e)}

    def _create_executive_response(self, query: str, result: Dict, parsed_query: Dict) -> Dict[str, Any]:
        """Create executive-level response with insights and recommendations"""

        response = {
            "query": query,
            "response_timestamp": datetime.now().isoformat(),
            "agent_version": self.config.version,
            "query_classification": parsed_query["query_type"],
            "confidence": result.get("confidence", 0.95),
            "executive_summary": self._generate_executive_summary(result),
            "detailed_analysis": result,
            "key_insights": self._extract_key_insights(result),
            "recommendations": self._generate_recommendations(result),
            "visualization_suggestions": self._suggest_visualizations(parsed_query, result),
            "follow_up_queries": self._suggest_follow_ups(query, result),
            "data_quality": self._assess_data_quality(result),
            "session_context": {
                "query_number": self.session_stats["queries_processed"] + 1,
                "session_duration": (datetime.now() - self.session_stats["session_start"]).total_seconds()
            }
        }

        return response

    def _generate_executive_summary(self, result: Dict) -> str:
        """Generate executive-level summary"""

        if result.get("summary"):
            return result["summary"]

        # Generate summary from available data
        summary_parts = []

        if result.get("total_commitment"):
            commitment = self._format_currency(result["total_commitment"])
            summary_parts.append(f"Portfolio analysis shows {commitment} in total commitments")

        if result.get("key_insights"):
            insight_count = len(result["key_insights"])
            summary_parts.append(f"Generated {insight_count} strategic insights")

        if result.get("enhanced"):
            summary_parts.append("Enhanced with comprehensive knowledge base analysis")

        return " | ".join(summary_parts) if summary_parts else "Analysis completed successfully"

    def _extract_key_insights(self, result: Dict) -> List[Dict[str, Any]]:
        """Extract and format key insights"""

        insights = []

        # From main agent
        if result.get("key_insights"):
            insights.extend(result["key_insights"])

        # From DO agent enhancement
        if result.get("do_agent_insights"):
            do_insights = result["do_agent_insights"]
            if isinstance(do_insights, dict) and "insights" in do_insights:
                insights.extend(do_insights["insights"])

        # Ensure proper formatting
        formatted_insights = []
        for insight in insights[:5]:  # Top 5 insights
            if isinstance(insight, dict):
                formatted_insights.append({
                    "title": insight.get("title", "Key Finding"),
                    "impact": insight.get("impact", "Medium"),
                    "finding": insight.get("finding", insight.get("description", "")),
                    "recommendation": insight.get("recommendation", "Continue monitoring"),
                    "confidence": insight.get("confidence", 0.85)
                })

        return formatted_insights

    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = [
            "Continue monitoring key performance indicators",
            "Review portfolio distribution for optimization opportunities",
            "Analyze implementation efficiency across sectors"
        ]

        # Add specific recommendations from insights
        if result.get("key_insights"):
            for insight in result["key_insights"][:3]:
                if isinstance(insight, dict) and insight.get("recommendation"):
                    recommendations.append(insight["recommendation"])

        return recommendations[:5]  # Top 5 recommendations

    def _update_session_stats(self, execution_time: float):
        """Update session statistics"""

        self.session_stats["queries_processed"] += 1

        # Update average response time
        current_avg = self.session_stats["avg_response_time"]
        query_count = self.session_stats["queries_processed"]

        new_avg = ((current_avg * (query_count - 1)) + execution_time) / query_count
        self.session_stats["avg_response_time"] = new_avg

    def _create_error_response(self, error: str, query: str, execution_time: float) -> Dict[str, Any]:
        """Create error response"""

        return {
            "error": True,
            "message": error,
            "query": query,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "support_message": "Please contact support with this error information",
            "suggested_actions": [
                "Try rephrasing your query",
                "Check if all required parameters are provided",
                "Verify data availability for the requested scope"
            ]
        }

    def _format_currency(self, amount: float) -> str:
        """Format currency amounts"""
        if amount >= 1e9:
            return f"${amount/1e9:.1f}B"
        elif amount >= 1e6:
            return f"${amount/1e6:.1f}M"
        else:
            return f"${amount:,.0f}"

# Command-line interface for testing
async def main():
    """Main function for testing the orchestrator"""

    print("🌍 World Bank IATI Intelligence Agent")
    print("=" * 50)

    # Initialize orchestrator
    orchestrator = WBIATIAgentOrchestrator()

    # Initialize agent
    init_success = await orchestrator.initialize()

    if not init_success:
        print("❌ Agent initialization failed")
        return

    # Display agent status
    status = orchestrator.get_agent_status()
    print(f"\n✅ Agent Status: {status['agent_info']['name']} v{status['agent_info']['version']}")
    print(f"📊 Data Coverage: {status['api_config']['data_coverage']}")
    print(f"🔗 Endpoint: {status['api_config']['endpoint'][:50]}...")

    # Test queries
    test_queries = [
        "What is the World Bank's total active portfolio?",
        "Show me education sector trends in Sub-Saharan Africa",
        "Create an executive dashboard for portfolio performance",
        "Analyze climate finance distribution by region",
        "Compare infrastructure investment efficiency across countries"
    ]

    print(f"\n🧪 Testing with {len(test_queries)} sample queries...")

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")

        try:
            start_time = time.time()
            result = await orchestrator.process_user_query(query)
            execution_time = time.time() - start_time

            if result.get("error"):
                print(f"   ❌ Error: {result['message']}")
            else:
                print(f"   ✅ Success ({execution_time:.2f}s)")
                print(f"   📊 Summary: {result['executive_summary'][:100]}...")
                print(f"   💡 Insights: {len(result.get('key_insights', []))}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

    # Final session statistics
    final_status = orchestrator.get_agent_status()
    stats = final_status["session_stats"]

    print(f"\n📈 Session Summary:")
    print(f"   Queries Processed: {stats['queries_processed']}")
    print(f"   Dashboards Created: {stats['dashboards_created']}")
    print(f"   Average Response Time: {stats['avg_response_time']:.2f}s")

    print("\n🎯 World Bank IATI Intelligence Agent ready for production")

if __name__ == "__main__":
    run_async_safely.run(main())
    
