"""
World Bank IATI Intelligence Agent Configuration
Enterprise-grade AI system for development finance data analysis
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class AgentConfig:
    """Core configuration for the WB IATI Intelligence Agent"""

    # API Configuration
    api_key: str = "3vgEVfMeM5_rggpNoeLpe0agHBAN42yD"
    endpoint: str = "https://mrngtcmmhzbbdopptwzoirop.agents.do-ai.run"
    chatbot_id: str = "1FV8wQ78ZHOndsmrfmaNXmjpxi-snRAW"

    # Agent Identity
    agent_name: str = "World Bank IATI Intelligence Agent"
    version: str = "1.0.0"
    description: str = "Advanced AI system for IATI registry data analysis and insights"

    # Core Mission Parameters
    data_coverage: str = "$50B+ annual commitments"
    countries_covered: int = 170
    data_sources: List[str] = None
    update_frequency: str = "Quarterly with real-time transactions"

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = [
                "IATI Registry",
                "World Bank Project Database",
                "IDA/IBRD Financial Data",
                "Trust Fund Registry",
                "Results Framework Database"
            ]

class IATIDataDimensions:
    """Standard IATI data dimensions and classifications"""

    FINANCIAL_FLOWS = [
        "commitments", "disbursements", "expenditures",
        "loan_terms", "grant_conditions", "co_financing"
    ]

    SECTORS = {
        "education": {"codes": ["110", "111", "112", "113"], "sdg": [4]},
        "health": {"codes": ["120", "121", "122", "123"], "sdg": [3]},
        "infrastructure": {"codes": ["210", "220", "230", "240"], "sdg": [6, 7, 9]},
        "climate": {"codes": ["410", "430", "432"], "sdg": [13, 14, 15]},
        "governance": {"codes": ["150", "151", "152"], "sdg": [16]}
    }

    REGIONS = [
        "Sub-Saharan Africa", "East Asia and Pacific", "Europe and Central Asia",
        "Latin America and Caribbean", "Middle East and North Africa", "South Asia"
    ]

    FRAGILITY_CLASSIFICATIONS = [
        "FCS", "SIDS", "LDC", "IDA", "IBRD", "Blend"
    ]

class DashboardTemplates:
    """Pre-configured dashboard templates for different stakeholder needs"""

    EXECUTIVE_OVERVIEW = {
        "title": "World Bank Portfolio Executive Dashboard",
        "components": [
            {"type": "kpi_cards", "metrics": ["total_commitment", "disbursement_ratio", "active_projects", "countries"]},
            {"type": "pie_chart", "data": "sector_distribution", "title": "Portfolio by Sector"},
            {"type": "line_chart", "data": "quarterly_disbursements", "title": "Disbursement Trends"},
            {"type": "map", "data": "geographic_distribution", "title": "Global Portfolio"},
            {"type": "bar_chart", "data": "top_10_countries", "title": "Largest Country Portfolios"}
        ],
        "filters": ["date_range", "sector", "region", "instrument_type"],
        "refresh_rate": "daily"
    }

    SECTOR_DEEP_DIVE = {
        "title": "Sector Analysis Dashboard",
        "components": [
            {"type": "timeline", "data": "sector_commitments", "title": "Commitment Timeline"},
            {"type": "heatmap", "data": "geographic_sector", "title": "Sector by Country"},
            {"type": "waterfall", "data": "subsector_breakdown", "title": "Sub-sector Analysis"},
            {"type": "gauge", "data": "results_indicators", "title": "Results Achievement"},
            {"type": "network", "data": "partner_mapping", "title": "Implementation Partners"}
        ],
        "dynamic_filters": True,
        "drill_down": True
    }

    COUNTRY_PORTFOLIO = {
        "title": "Country Portfolio Analysis",
        "components": [
            {"type": "project_list", "data": "active_projects", "sortable": True},
            {"type": "waterfall", "data": "commitment_disbursement", "title": "Financial Flow"},
            {"type": "donut", "data": "sector_composition", "title": "Sector Mix"},
            {"type": "gantt", "data": "project_timeline", "title": "Implementation Schedule"},
            {"type": "scorecard", "data": "results_framework", "title": "Development Results"}
        ],
        "country_selector": True,
        "comparison_mode": True
    }

class QueryPatterns:
    """Natural language query patterns and response frameworks"""

    FINANCIAL_QUERIES = {
        "patterns": [
            r"how much.*committed.*to.*(\w+).*in.*(\w+)",
            r"total.*disbursement.*for.*(\w+).*sector",
            r"compare.*spending.*between.*(\w+).*and.*(\w+)"
        ],
        "response_template": {
            "summary": "Financial summary with key metrics",
            "breakdown": "Detailed financial breakdown table",
            "context": "Historical comparison and benchmarks",
            "visualization": "Recommended chart type and data"
        }
    }

    SECTOR_QUERIES = {
        "patterns": [
            r"(\w+).*sector.*trends.*in.*(\w+)",
            r"show.*education.*projects.*in.*fragile.*states",
            r"climate.*finance.*distribution"
        ],
        "analysis_types": ["trend", "distribution", "comparison", "deep_dive"]
    }

    GEOGRAPHIC_QUERIES = {
        "patterns": [
            r"which.*countries.*highest.*disbursement",
            r"(\w+).*region.*portfolio.*analysis",
            r"sub-national.*distribution.*in.*(\w+)"
        ],
        "mapping_enabled": True,
        "drill_down_levels": ["global", "regional", "country", "subnational"]
    }

class AnalyticalCapabilities:
    """Core analytical functions and methodologies"""

    TREND_ANALYSIS = {
        "methods": ["yoy_growth", "seasonal_patterns", "portfolio_shifts"],
        "indicators": ["commitment_trend", "disbursement_velocity", "sector_evolution"],
        "forecasting": True
    }

    ANOMALY_DETECTION = {
        "algorithms": ["statistical_outliers", "pattern_breaks", "threshold_violations"],
        "alert_types": ["disbursement_delays", "concentration_risk", "performance_decline"],
        "confidence_levels": [0.95, 0.99]
    }

    COMPARATIVE_ANALYTICS = {
        "benchmark_types": ["peer_countries", "sector_averages", "regional_comparison"],
        "metrics": ["efficiency_ratios", "leverage_factors", "results_intensity"],
        "visualization": "comparative_charts"
    }

    PREDICTIVE_SIGNALS = {
        "models": ["disbursement_forecasting", "portfolio_risk", "results_prediction"],
        "horizon": ["6_months", "1_year", "3_years"],
        "confidence_intervals": True
    }

# Agent Response Protocols
class ResponseProtocols:
    """Standardized response formats and interaction patterns"""

    INSIGHT_FORMAT = """
    ## 🔍 Key Finding: {title}

    **What**: {insight_statement}
    **Impact**: {significance}
    **Evidence**: {data_points}
    **Context**: {benchmark}
    **Recommendation**: {next_action}
    """

    DATA_QUALITY_INDICATORS = {
        "completeness": {"threshold": 0.95, "warning": "Data gaps identified"},
        "freshness": {"max_age_days": 30, "warning": "Data may be outdated"},
        "consistency": {"variance_threshold": 0.1, "warning": "Inconsistencies detected"}
    }

    CONFIDENCE_LEVELS = {
        "high": "≥95% data coverage, recent update",
        "medium": "80-94% coverage, some limitations",
        "low": "<80% coverage, significant gaps"
    }

# Initialize configuration
def get_agent_config():
    """Return initialized agent configuration"""
    return AgentConfig()

def validate_api_connection(config: AgentConfig) -> bool:
    """Validate connection to Digital Ocean API endpoint"""
    try:
        import requests
        headers = {"Authorization": f"Bearer {config.api_key}"}
        response = requests.get(f"{config.endpoint}/health", headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"API connection validation failed: {e}")
        return False

if __name__ == "__main__":
    config = get_agent_config()
    print(f"World Bank IATI Intelligence Agent v{config.version}")
    print(f"Configured for {config.countries_covered}+ countries")
    print(f"Data coverage: {config.data_coverage}")