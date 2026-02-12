"""
Digital Ocean API Integration for World Bank IATI Intelligence Agent
Handles communication with the DO endpoint and chatbot integration
"""

import asyncio
import aiohttp
import requests
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import time
from dataclasses import dataclass

from wb_iati_agent_config import AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Standardized API response structure"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    execution_time: Optional[float] = None

class DigitalOceanAPI:
    """Digital Ocean API client for the WB IATI Intelligence Agent"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.base_url = config.endpoint
        self.api_key = config.api_key
        self.chatbot_id = config.chatbot_id

        # Session configuration
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"WB-IATI-Agent/{config.version}",
            "X-Chatbot-ID": self.chatbot_id
        })

        # Rate limiting
        self.rate_limit = {"requests_per_minute": 60, "last_request": 0, "request_count": 0}

        logger.info(f"🚀 Digital Ocean API client initialized for endpoint: {self.base_url}")

    async def health_check(self) -> APIResponse:
        """Check API endpoint health and connectivity"""

        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            execution_time = time.time() - start_time

            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    data={"status": "healthy", "endpoint": self.base_url},
                    status_code=response.status_code,
                    execution_time=execution_time
                )
            else:
                return APIResponse(
                    success=False,
                    error=f"Health check failed with status {response.status_code}",
                    status_code=response.status_code,
                    execution_time=execution_time
                )

        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            logger.error(f"Health check failed: {e}")
            return APIResponse(
                success=False,
                error=f"Connection failed: {str(e)}",
                execution_time=execution_time
            )

    async def send_query(self, query: str, context: Dict = None) -> APIResponse:
        """Send query to the Digital Ocean agent endpoint"""

        # Rate limiting check
        self._check_rate_limit()

        payload = {
            "query": query,
            "chatbot_id": self.chatbot_id,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "session_id": f"wb_iati_{int(time.time())}"
        }

        start_time = time.time()
        try:
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )

            execution_time = time.time() - start_time
            self._update_rate_limit()

            if response.status_code == 200:
                response_data = response.json()
                return APIResponse(
                    success=True,
                    data=response_data,
                    status_code=response.status_code,
                    execution_time=execution_time
                )
            else:
                logger.error(f"Query failed with status {response.status_code}: {response.text}")
                return APIResponse(
                    success=False,
                    error=f"Query failed: {response.status_code}",
                    status_code=response.status_code,
                    execution_time=execution_time
                )

        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            logger.error(f"Query request failed: {e}")
            return APIResponse(
                success=False,
                error=f"Request failed: {str(e)}",
                execution_time=execution_time
            )

    async def get_agent_capabilities(self) -> APIResponse:
        """Retrieve agent capabilities and available functions"""

        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/capabilities", timeout=15)
            execution_time = time.time() - start_time

            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    data=response.json(),
                    status_code=response.status_code,
                    execution_time=execution_time
                )
            else:
                return APIResponse(
                    success=False,
                    error=f"Failed to get capabilities: {response.status_code}",
                    status_code=response.status_code,
                    execution_time=execution_time
                )

        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            return APIResponse(
                success=False,
                error=f"Capabilities request failed: {str(e)}",
                execution_time=execution_time
            )

    async def stream_response(self, query: str, context: Dict = None) -> AsyncGenerator[Dict, None]:
        """Stream responses for long-running analyses"""

        payload = {
            "query": query,
            "chatbot_id": self.chatbot_id,
            "context": context or {},
            "stream": True,
            "timestamp": datetime.now().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                async with session.post(
                    f"{self.base_url}/stream",
                    json=payload,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        async for line in response.content:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                yield chunk
                            except json.JSONDecodeError:
                                continue
                    else:
                        yield {"error": f"Stream failed with status {response.status}"}

        except Exception as e:
            yield {"error": f"Stream connection failed: {str(e)}"}

    def _check_rate_limit(self):
        """Check and enforce rate limiting"""

        current_time = time.time()
        if current_time - self.rate_limit["last_request"] > 60:
            # Reset counter after 1 minute
            self.rate_limit["request_count"] = 0

        if self.rate_limit["request_count"] >= self.rate_limit["requests_per_minute"]:
            sleep_time = 60 - (current_time - self.rate_limit["last_request"])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.rate_limit["request_count"] = 0

    def _update_rate_limit(self):
        """Update rate limit tracking"""
        self.rate_limit["last_request"] = time.time()
        self.rate_limit["request_count"] += 1

class ChatbotInterface:
    """High-level interface for chatbot interactions"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.api_client = DigitalOceanAPI(config)
        self.conversation_history = []

        logger.info(f"💬 Chatbot interface initialized for agent: {config.chatbot_id}")

    async def initialize_session(self) -> bool:
        """Initialize chatbot session and validate connectivity"""

        health_result = await self.api_client.health_check()

        if health_result.success:
            # Get agent capabilities
            caps_result = await self.api_client.get_agent_capabilities()

            if caps_result.success:
                logger.info("✅ Chatbot session initialized successfully")
                logger.info(f"📊 Agent capabilities: {caps_result.data}")
                return True

        logger.error("❌ Failed to initialize chatbot session")
        return False

    async def send_iati_query(self, query: str, include_visualizations: bool = True) -> Dict[str, Any]:
        """Send IATI-specific query with enhanced context"""

        # Prepare enhanced context for IATI queries
        context = {
            "domain": "world_bank_iati",
            "data_sources": self.config.data_sources,
            "include_visualizations": include_visualizations,
            "response_format": "executive_summary",
            "confidence_required": True,
            "session_history": len(self.conversation_history)
        }

        # Send query
        result = await self.api_client.send_query(query, context)

        # Store in conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "success": result.success,
            "execution_time": result.execution_time
        })

        if result.success:
            return {
                "response": result.data,
                "metadata": {
                    "execution_time": result.execution_time,
                    "confidence": result.data.get("confidence", 0.95),
                    "data_sources": context["data_sources"],
                    "query_complexity": self._assess_query_complexity(query)
                }
            }
        else:
            return {
                "error": result.error,
                "metadata": {
                    "execution_time": result.execution_time,
                    "retry_recommended": True
                }
            }

    async def create_dashboard_request(self, dashboard_type: str, parameters: Dict) -> Dict[str, Any]:
        """Request dashboard creation through the API"""

        dashboard_query = f"Create a {dashboard_type} dashboard with the following parameters: {json.dumps(parameters)}"

        context = {
            "request_type": "dashboard_creation",
            "dashboard_type": dashboard_type,
            "parameters": parameters,
            "output_format": "dashboard_config"
        }

        result = await self.api_client.send_query(dashboard_query, context)

        if result.success:
            return {
                "dashboard_config": result.data,
                "creation_time": result.execution_time,
                "status": "ready"
            }
        else:
            return {
                "error": result.error,
                "status": "failed"
            }

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation history"""

        if not self.conversation_history:
            return {"status": "no_conversation"}

        total_queries = len(self.conversation_history)
        successful_queries = sum(1 for q in self.conversation_history if q["success"])
        avg_execution_time = sum(q["execution_time"] or 0 for q in self.conversation_history) / total_queries

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "average_execution_time": avg_execution_time,
            "session_duration": self._calculate_session_duration(),
            "last_query": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }

    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of the query"""

        complexity_indicators = [
            "compare", "analyze", "trend", "correlation",
            "breakdown", "distribution", "efficiency", "impact"
        ]

        query_lower = query.lower()
        score = sum(1 for indicator in complexity_indicators if indicator in query_lower)

        if score >= 4:
            return "very_high"
        elif score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        elif score >= 1:
            return "low"
        else:
            return "simple"

    def _calculate_session_duration(self) -> Optional[float]:
        """Calculate total session duration"""

        if len(self.conversation_history) < 2:
            return None

        start_time = datetime.fromisoformat(self.conversation_history[0]["timestamp"])
        end_time = datetime.fromisoformat(self.conversation_history[-1]["timestamp"])

        return (end_time - start_time).total_seconds()

# Connection testing and validation
async def test_connection(config: AgentConfig) -> Dict[str, Any]:
    """Test all API connections and functionality"""

    print("🔍 Testing Digital Ocean API connection...")

    test_results = {
        "health_check": None,
        "capabilities": None,
        "sample_query": None,
        "overall_status": "unknown"
    }

    api_client = DigitalOceanAPI(config)

    # Test 1: Health check
    print("  1. Health check...")
    health_result = await api_client.health_check()
    test_results["health_check"] = {
        "success": health_result.success,
        "execution_time": health_result.execution_time,
        "error": health_result.error
    }

    if health_result.success:
        print("  ✅ Health check passed")
    else:
        print(f"  ❌ Health check failed: {health_result.error}")

    # Test 2: Capabilities
    print("  2. Capabilities check...")
    caps_result = await api_client.get_agent_capabilities()
    test_results["capabilities"] = {
        "success": caps_result.success,
        "execution_time": caps_result.execution_time,
        "error": caps_result.error
    }

    if caps_result.success:
        print("  ✅ Capabilities retrieved")
    else:
        print(f"  ❌ Capabilities failed: {caps_result.error}")

    # Test 3: Sample query
    print("  3. Sample query test...")
    sample_query = "What is the total World Bank portfolio size?"
    query_result = await api_client.send_query(sample_query)
    test_results["sample_query"] = {
        "success": query_result.success,
        "execution_time": query_result.execution_time,
        "error": query_result.error
    }

    if query_result.success:
        print("  ✅ Sample query succeeded")
    else:
        print(f"  ❌ Sample query failed: {query_result.error}")

    # Overall status
    all_tests_passed = all(
        test_results[test]["success"] for test in test_results
        if test != "overall_status" and test_results[test] is not None
    )

    test_results["overall_status"] = "passed" if all_tests_passed else "failed"

    print(f"\n🎯 Overall connection test: {'✅ PASSED' if all_tests_passed else '❌ FAILED'}")

    return test_results

# Main execution for testing
if __name__ == "__main__":
    config = AgentConfig()

    async def main():
        # Test connection
        test_result = await test_connection(config)

        if test_result["overall_status"] == "passed":
            print("\n🚀 Initializing chatbot interface...")
            chatbot = ChatbotInterface(config)

            session_init = await chatbot.initialize_session()
            if session_init:
                print("✅ Chatbot interface ready for queries")

                # Example usage
                sample_queries = [
                    "What is the World Bank's total active portfolio?",
                    "Show me education sector commitments in Sub-Saharan Africa",
                    "Create an executive dashboard for FY2024 performance"
                ]

                for query in sample_queries:
                    print(f"\n🔍 Testing query: '{query}'")
                    result = await chatbot.send_iati_query(query)

                    if "response" in result:
                        print(f"✅ Query successful (took {result['metadata']['execution_time']:.2f}s)")
                    else:
                        print(f"❌ Query failed: {result.get('error', 'Unknown error')}")

                # Show conversation summary
                summary = chatbot.get_conversation_summary()
                print(f"\n📊 Session Summary:")
                print(f"  Queries: {summary['total_queries']}")
                print(f"  Success rate: {summary['success_rate']:.1%}")
                print(f"  Avg execution time: {summary['average_execution_time']:.2f}s")

    asyncio.run(main())