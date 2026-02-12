"""
World Bank IATI Intelligence Agent
Main agent class with natural language processing and analytical capabilities
"""

import re
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import requests
from dataclasses import dataclass, asdict

from wb_iati_agent_config import (
    AgentConfig, IATIDataDimensions, DashboardTemplates,
    QueryPatterns, AnalyticalCapabilities, ResponseProtocols
)

class WBIATIIntelligenceAgent:
    """
    World Bank IATI Intelligence Agent
    Enterprise-grade AI system for development finance data analysis
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })

        # Initialize analytical modules
        self.query_processor = QueryProcessor()
        self.insight_generator = InsightGenerator()
        self.dashboard_builder = DashboardBuilder()
        self.data_validator = DataValidator()

        print(f"🌍 {self.config.agent_name} v{self.config.version} initialized")
        print(f"📊 Ready to analyze {self.config.data_coverage} across {self.config.countries_covered}+ countries")

    async def process_query(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        Main entry point for processing natural language queries

        Args:
            query (str): Natural language question about IATI data
            user_context (Dict): Optional user context and preferences

        Returns:
            Dict: Structured response with analysis, visualizations, and insights
        """
        # Step 1: Parse and understand the query
        parsed_query = self.query_processor.parse_natural_language(query)

        # Step 2: Validate data availability and scope
        validation_result = self.data_validator.validate_query_scope(parsed_query)

        if not validation_result["valid"]:
            return self._create_error_response(validation_result["message"], query)

        # Step 3: Execute data analysis
        analysis_result = await self._execute_analysis(parsed_query)

        # Step 4: Generate insights and recommendations
        insights = self.insight_generator.generate_insights(analysis_result)

        # Step 5: Create visualization recommendations
        viz_recommendations = self.dashboard_builder.recommend_visualizations(
            analysis_result, parsed_query["intent"]
        )

        # Step 6: Format comprehensive response
        response = self._format_response(
            query=query,
            analysis=analysis_result,
            insights=insights,
            visualizations=viz_recommendations,
            confidence=validation_result["confidence"]
        )

        return response

    def create_dashboard(self, dashboard_type: str, parameters: Dict = None) -> Dict[str, Any]:
        """
        Generate executive dashboards for different stakeholder needs

        Args:
            dashboard_type (str): Type of dashboard (executive, sector, country, thematic)
            parameters (Dict): Dashboard-specific parameters

        Returns:
            Dict: Dashboard configuration and data structure
        """
        return self.dashboard_builder.create_dashboard(dashboard_type, parameters)

    def get_portfolio_overview(self, filters: Dict = None) -> Dict[str, Any]:
        """Quick portfolio overview with key metrics"""

        default_filters = {
            "date_range": "last_12_months",
            "status": "active",
            "publisher": "World Bank"
        }

        if filters:
            default_filters.update(filters)

        # Simulate portfolio data (in real implementation, this would query IATI API)
        portfolio_data = {
            "total_commitment": 47.3e9,  # $47.3B
            "total_disbursement": 34.7e9,  # $34.7B
            "disbursement_ratio": 0.733,  # 73.3%
            "active_projects": 892,
            "countries": 127,
            "sectors_count": 23,
            "avg_project_size": 53.0e6,  # $53M average
            "top_sectors": [
                {"sector": "Infrastructure", "commitment": 12.4e9, "percentage": 26.2},
                {"sector": "Health", "commitment": 8.7e9, "percentage": 18.4},
                {"sector": "Education", "commitment": 7.2e9, "percentage": 15.2},
                {"sector": "Climate", "commitment": 6.8e9, "percentage": 14.4},
                {"sector": "Governance", "commitment": 4.9e9, "percentage": 10.4}
            ],
            "top_countries": [
                {"country": "India", "commitment": 8.2e9, "projects": 127},
                {"country": "Nigeria", "commitment": 3.4e9, "projects": 89},
                {"country": "Bangladesh", "commitment": 2.8e9, "projects": 76},
                {"country": "Indonesia", "commitment": 2.6e9, "projects": 52},
                {"country": "Pakistan", "commitment": 2.1e9, "projects": 67}
            ]
        }

        return {
            "summary": self._format_portfolio_summary(portfolio_data),
            "data": portfolio_data,
            "last_updated": datetime.now().isoformat(),
            "data_quality": {"completeness": 0.97, "freshness": "current"}
        }

    async def _execute_analysis(self, parsed_query: Dict) -> Dict[str, Any]:
        """Execute the actual data analysis based on parsed query"""

        analysis_type = parsed_query["intent"]
        entities = parsed_query["entities"]

        # Route to appropriate analysis method
        if analysis_type == "financial_analysis":
            return await self._analyze_financial_data(entities)
        elif analysis_type == "sector_analysis":
            return await self._analyze_sector_data(entities)
        elif analysis_type == "geographic_analysis":
            return await self._analyze_geographic_data(entities)
        elif analysis_type == "trend_analysis":
            return await self._analyze_trends(entities)
        elif analysis_type == "comparative_analysis":
            return await self._analyze_comparative(entities)
        else:
            return await self._general_analysis(entities)

    async def _analyze_financial_data(self, entities: Dict) -> Dict[str, Any]:
        """Analyze financial flows and commitments"""

        # Simulate financial analysis (real implementation would query IATI database)
        mock_data = {
            "total_commitment": 47.3e9,
            "total_disbursement": 34.7e9,
            "disbursement_efficiency": 0.733,
            "quarterly_trends": [
                {"quarter": "2024-Q1", "commitment": 11.2e9, "disbursement": 8.4e9},
                {"quarter": "2024-Q2", "commitment": 12.8e9, "disbursement": 9.1e9},
                {"quarter": "2024-Q3", "commitment": 13.1e9, "disbursement": 8.9e9},
                {"quarter": "2024-Q4", "commitment": 10.2e9, "disbursement": 8.3e9}
            ],
            "instrument_breakdown": {
                "IDA_Credits": {"amount": 23.8e9, "percentage": 50.3},
                "IBRD_Loans": {"amount": 15.2e9, "percentage": 32.1},
                "Trust_Funds": {"amount": 5.8e9, "percentage": 12.3},
                "Grants": {"amount": 2.5e9, "percentage": 5.3}
            }
        }

        return {
            "analysis_type": "financial",
            "data": mock_data,
            "key_metrics": self._extract_financial_insights(mock_data),
            "confidence": 0.95
        }

    def _format_response(self, query: str, analysis: Dict, insights: List,
                        visualizations: List, confidence: float) -> Dict[str, Any]:
        """Format the final response to the user"""

        response = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "summary": self._create_executive_summary(analysis, insights),
            "detailed_analysis": analysis,
            "key_insights": insights,
            "recommended_visualizations": visualizations,
            "follow_up_suggestions": self._generate_follow_ups(query, analysis),
            "data_sources": self.config.data_sources,
            "methodology": "IATI standard aggregation with World Bank validation"
        }

        return response

    def _create_executive_summary(self, analysis: Dict, insights: List) -> str:
        """Create executive summary of the analysis"""

        summary_parts = []

        if analysis.get("data"):
            data = analysis["data"]
            if "total_commitment" in data:
                commitment = self._format_currency(data["total_commitment"])
                summary_parts.append(f"Total portfolio: {commitment} in commitments")

            if "disbursement_efficiency" in data:
                efficiency = f"{data['disbursement_efficiency']:.1%}"
                summary_parts.append(f"Disbursement rate: {efficiency}")

        if insights:
            key_insight = insights[0] if insights else None
            if key_insight:
                summary_parts.append(f"Key finding: {key_insight.get('title', 'Analysis completed')}")

        return " | ".join(summary_parts) if summary_parts else "Analysis completed successfully"

    def _format_currency(self, amount: float) -> str:
        """Format currency amounts for display"""
        if amount >= 1e9:
            return f"${amount/1e9:.1f}B"
        elif amount >= 1e6:
            return f"${amount/1e6:.1f}M"
        elif amount >= 1e3:
            return f"${amount/1e3:.1f}K"
        else:
            return f"${amount:.0f}"

    def _format_portfolio_summary(self, data: Dict) -> str:
        """Format portfolio data into executive summary"""

        commitment = self._format_currency(data["total_commitment"])
        disbursement = self._format_currency(data["total_disbursement"])
        ratio = f"{data['disbursement_ratio']:.1%}"
        projects = data["active_projects"]
        countries = data["countries"]

        return (f"World Bank portfolio: {commitment} committed, {disbursement} disbursed "
               f"({ratio} efficiency) across {projects} active projects in {countries} countries")

class QueryProcessor:
    """Natural language query processing and intent recognition"""

    def __init__(self):
        self.patterns = QueryPatterns()

    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """Parse natural language query into structured analysis request"""

        query_lower = query.lower()

        # Intent recognition
        intent = self._identify_intent(query_lower)

        # Entity extraction
        entities = self._extract_entities(query_lower)

        # Parameter extraction
        parameters = self._extract_parameters(query_lower)

        return {
            "original_query": query,
            "intent": intent,
            "entities": entities,
            "parameters": parameters,
            "complexity": self._assess_complexity(query_lower)
        }

    def _identify_intent(self, query: str) -> str:
        """Identify the primary intent of the query"""

        if any(word in query for word in ["how much", "total", "amount", "spent", "committed"]):
            return "financial_analysis"
        elif any(word in query for word in ["sector", "education", "health", "infrastructure"]):
            return "sector_analysis"
        elif any(word in query for word in ["country", "region", "where", "geographic"]):
            return "geographic_analysis"
        elif any(word in query for word in ["trend", "over time", "growth", "change"]):
            return "trend_analysis"
        elif any(word in query for word in ["compare", "versus", "vs", "between"]):
            return "comparative_analysis"
        else:
            return "general_analysis"

    def _extract_entities(self, query: str) -> Dict[str, List]:
        """Extract relevant entities from the query"""

        entities = {
            "countries": [],
            "sectors": [],
            "regions": [],
            "time_periods": [],
            "instruments": []
        }

        # Country extraction (simplified - real implementation would use NER)
        countries = ["india", "nigeria", "bangladesh", "indonesia", "pakistan", "kenya", "ethiopia"]
        for country in countries:
            if country in query:
                entities["countries"].append(country.title())

        # Sector extraction
        sectors = ["education", "health", "infrastructure", "climate", "governance", "agriculture"]
        for sector in sectors:
            if sector in query:
                entities["sectors"].append(sector.title())

        # Region extraction
        regions = ["africa", "asia", "latin america", "middle east", "europe"]
        for region in regions:
            if region in query:
                entities["regions"].append(region.title())

        return entities

    def _extract_parameters(self, query: str) -> Dict[str, Any]:
        """Extract query parameters and filters"""

        parameters = {
            "aggregation_level": "country",
            "time_range": "last_12_months",
            "currency": "USD",
            "include_pipeline": False
        }

        # Time range extraction
        if "since 2020" in query:
            parameters["time_range"] = "2020-present"
        elif "last year" in query:
            parameters["time_range"] = "last_12_months"
        elif "this year" in query:
            parameters["time_range"] = "current_year"

        return parameters

    def _assess_complexity(self, query: str) -> str:
        """Assess the complexity of the query"""

        complexity_indicators = [
            "compare", "analyze", "trend", "correlation",
            "breakdown", "distribution", "efficiency"
        ]

        score = sum(1 for indicator in complexity_indicators if indicator in query)

        if score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"

class InsightGenerator:
    """Generate actionable insights from data analysis"""

    def generate_insights(self, analysis_result: Dict) -> List[Dict[str, Any]]:
        """Generate insights from analysis results"""

        insights = []

        if analysis_result["analysis_type"] == "financial":
            insights.extend(self._financial_insights(analysis_result["data"]))

        # Add trend insights
        insights.extend(self._trend_insights(analysis_result))

        # Add comparative insights
        insights.extend(self._comparative_insights(analysis_result))

        return insights

    def _financial_insights(self, data: Dict) -> List[Dict[str, Any]]:
        """Generate financial analysis insights"""

        insights = []

        if "disbursement_efficiency" in data:
            efficiency = data["disbursement_efficiency"]

            if efficiency > 0.8:
                insights.append({
                    "title": "Strong Disbursement Performance",
                    "impact": "High",
                    "finding": f"Portfolio shows {efficiency:.1%} disbursement efficiency",
                    "implication": "Excellent project implementation and financial management",
                    "recommendation": "Maintain current practices and share lessons learned"
                })
            elif efficiency < 0.6:
                insights.append({
                    "title": "Disbursement Efficiency Concern",
                    "impact": "High",
                    "finding": f"Portfolio disbursement rate at {efficiency:.1%}",
                    "implication": "Potential implementation delays or capacity constraints",
                    "recommendation": "Review project readiness and implementation support"
                })

        return insights

class DashboardBuilder:
    """Build and configure dashboards for different user needs"""

    def __init__(self):
        self.templates = DashboardTemplates()

    def create_dashboard(self, dashboard_type: str, parameters: Dict = None) -> Dict[str, Any]:
        """Create dashboard configuration based on type and parameters"""

        if dashboard_type == "executive":
            return self._create_executive_dashboard(parameters)
        elif dashboard_type == "sector":
            return self._create_sector_dashboard(parameters)
        elif dashboard_type == "country":
            return self._create_country_dashboard(parameters)
        else:
            return self._create_custom_dashboard(dashboard_type, parameters)

    def recommend_visualizations(self, analysis: Dict, intent: str) -> List[Dict[str, Any]]:
        """Recommend appropriate visualizations based on analysis and intent"""

        recommendations = []

        if intent == "financial_analysis":
            recommendations.extend([
                {"type": "waterfall_chart", "title": "Commitment to Disbursement Flow", "priority": "high"},
                {"type": "time_series", "title": "Quarterly Financial Trends", "priority": "medium"},
                {"type": "pie_chart", "title": "Instrument Distribution", "priority": "low"}
            ])
        elif intent == "sector_analysis":
            recommendations.extend([
                {"type": "horizontal_bar", "title": "Sector Commitment Ranking", "priority": "high"},
                {"type": "heatmap", "title": "Sector-Country Matrix", "priority": "medium"}
            ])
        elif intent == "geographic_analysis":
            recommendations.extend([
                {"type": "choropleth_map", "title": "Global Portfolio Distribution", "priority": "high"},
                {"type": "bubble_chart", "title": "Country Portfolio Size vs Performance", "priority": "medium"}
            ])

        return recommendations

    def _create_executive_dashboard(self, parameters: Dict) -> Dict[str, Any]:
        """Create executive overview dashboard"""

        return {
            "dashboard_id": f"executive_{datetime.now().strftime('%Y%m%d')}",
            "title": "World Bank Portfolio Executive Dashboard",
            "layout": self.templates.EXECUTIVE_OVERVIEW,
            "data_refresh": "real_time",
            "export_options": ["pdf", "powerpoint", "excel"],
            "sharing": {"public": False, "stakeholders": ["management", "board"]},
            "mobile_optimized": True
        }

class DataValidator:
    """Validate data queries and ensure quality standards"""

    def validate_query_scope(self, parsed_query: Dict) -> Dict[str, Any]:
        """Validate that the query can be fulfilled with available data"""

        validation_result = {
            "valid": True,
            "confidence": 1.0,
            "limitations": [],
            "message": "Query validated successfully"
        }

        # Check entity availability
        entities = parsed_query["entities"]

        if entities["countries"] and len(entities["countries"]) > 50:
            validation_result["limitations"].append("Large country set may affect performance")
            validation_result["confidence"] *= 0.9

        if entities["sectors"] and "Custom" in entities["sectors"]:
            validation_result["limitations"].append("Custom sector definitions may have limited data")
            validation_result["confidence"] *= 0.8

        return validation_result

# Utility functions
def format_insight_response(insight: Dict[str, Any]) -> str:
    """Format insight using the standard template"""

    template = ResponseProtocols.INSIGHT_FORMAT

    return template.format(
        title=insight.get("title", "Analysis Result"),
        insight_statement=insight.get("finding", "Analysis completed"),
        significance=insight.get("impact", "Medium"),
        data_points=insight.get("evidence", "Based on available data"),
        benchmark=insight.get("context", "Compared to portfolio average"),
        next_action=insight.get("recommendation", "Continue monitoring")
    )

# Main execution
if __name__ == "__main__":
    agent = WBIATIIntelligenceAgent()

    # Example usage
    sample_query = "How much has the World Bank committed to education projects in Sub-Saharan Africa since 2020?"

    print(f"\n🔍 Processing query: '{sample_query}'")

    # Simulate async execution
    import asyncio

    async def demo():
        result = await agent.process_query(sample_query)
        print(f"\n📊 Analysis Result:")
        print(f"Summary: {result['summary']}")
        print(f"Confidence: {result['confidence']:.1%}")
        print(f"Insights: {len(result['key_insights'])} key findings")
        print(f"Visualizations: {len(result['recommended_visualizations'])} recommended")

    asyncio.run(demo())