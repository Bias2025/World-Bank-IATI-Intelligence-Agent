"""
Advanced Analytics Module for World Bank IATI Intelligence Agent
Sophisticated analytical capabilities for trend analysis, anomaly detection, and predictive insights
"""

import numpy as np
import pandas as pd
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class AnalyticalResult:
    """Standardized analytical result structure"""
    analysis_type: str
    confidence: float
    insights: List[Dict[str, Any]]
    recommendations: List[str]
    data_summary: Dict[str, Any]
    methodology: str
    limitations: List[str]
    execution_time: float

@dataclass
class TrendAnalysis:
    """Trend analysis result structure"""
    trend_direction: str  # increasing, decreasing, stable, volatile
    trend_strength: float  # 0-1 scale
    seasonal_patterns: Dict[str, Any]
    breakpoints: List[Dict[str, Any]]
    forecast: Optional[Dict[str, Any]]
    trend_significance: float

class AdvancedQueryProcessor:
    """Advanced natural language query processing with domain expertise"""

    def __init__(self):
        self.sector_keywords = self._initialize_sector_mapping()
        self.financial_indicators = self._initialize_financial_indicators()
        self.geographic_entities = self._initialize_geographic_mapping()
        self.temporal_patterns = self._initialize_temporal_patterns()

    def parse_complex_query(self, query: str) -> Dict[str, Any]:
        """Parse complex multi-dimensional queries with contextual understanding"""

        parsed = {
            "query_type": self._classify_query_type(query),
            "entities": self._extract_entities_advanced(query),
            "intent": self._determine_analytical_intent(query),
            "complexity": self._assess_query_complexity(query),
            "required_analytics": self._identify_required_analytics(query),
            "visualization_hints": self._extract_visualization_hints(query),
            "stakeholder_context": self._infer_stakeholder_context(query)
        }

        return parsed

    def _classify_query_type(self, query: str) -> str:
        """Classify query into analytical categories"""

        query_lower = query.lower()

        # Financial analysis patterns
        if any(pattern in query_lower for pattern in [
            "commitment", "disbursement", "spending", "budget", "allocation", "financing"
        ]):
            return "financial_analysis"

        # Performance analysis patterns
        elif any(pattern in query_lower for pattern in [
            "performance", "efficiency", "results", "outcome", "impact", "effectiveness"
        ]):
            return "performance_analysis"

        # Trend analysis patterns
        elif any(pattern in query_lower for pattern in [
            "trend", "over time", "change", "growth", "decline", "pattern", "forecast"
        ]):
            return "trend_analysis"

        # Comparative analysis patterns
        elif any(pattern in query_lower for pattern in [
            "compare", "versus", "vs", "between", "difference", "relative"
        ]):
            return "comparative_analysis"

        # Risk analysis patterns
        elif any(pattern in query_lower for pattern in [
            "risk", "concentration", "vulnerability", "fragility", "stability"
        ]):
            return "risk_analysis"

        # Geographic analysis patterns
        elif any(pattern in query_lower for pattern in [
            "where", "geographic", "regional", "country", "location", "distribution"
        ]):
            return "geographic_analysis"

        else:
            return "exploratory_analysis"

    def _extract_entities_advanced(self, query: str) -> Dict[str, List[str]]:
        """Extract entities with contextual understanding and disambiguation"""

        entities = {
            "sectors": [],
            "countries": [],
            "regions": [],
            "instruments": [],
            "indicators": [],
            "time_periods": [],
            "stakeholders": []
        }

        query_lower = query.lower()

        # Sector extraction with synonym matching
        for sector, synonyms in self.sector_keywords.items():
            if any(synonym in query_lower for synonym in synonyms):
                entities["sectors"].append(sector)

        # Financial indicator extraction
        for indicator, patterns in self.financial_indicators.items():
            if any(pattern in query_lower for pattern in patterns):
                entities["indicators"].append(indicator)

        # Geographic entity extraction
        for geo_type, geo_list in self.geographic_entities.items():
            for geo_entity in geo_list:
                if geo_entity.lower() in query_lower:
                    entities[f"{geo_type}s"].append(geo_entity)

        # Temporal entity extraction
        time_matches = self._extract_temporal_entities(query_lower)
        entities["time_periods"] = time_matches

        return entities

    def _determine_analytical_intent(self, query: str) -> Dict[str, Any]:
        """Determine specific analytical intent and required methodologies"""

        query_lower = query.lower()

        intent = {
            "primary_objective": "unknown",
            "analytical_methods": [],
            "output_requirements": [],
            "stakeholder_level": "operational"
        }

        # Determine primary objective
        if any(word in query_lower for word in ["overview", "summary", "dashboard"]):
            intent["primary_objective"] = "overview"
            intent["stakeholder_level"] = "executive"
        elif any(word in query_lower for word in ["deep dive", "detailed", "analysis"]):
            intent["primary_objective"] = "deep_analysis"
            intent["stakeholder_level"] = "analytical"
        elif any(word in query_lower for word in ["monitor", "track", "alert"]):
            intent["primary_objective"] = "monitoring"
            intent["stakeholder_level"] = "operational"

        # Determine analytical methods needed
        if "trend" in query_lower:
            intent["analytical_methods"].append("trend_analysis")
        if any(word in query_lower for word in ["compare", "benchmark"]):
            intent["analytical_methods"].append("comparative_analysis")
        if any(word in query_lower for word in ["predict", "forecast", "project"]):
            intent["analytical_methods"].append("predictive_analysis")
        if "anomaly" in query_lower or "unusual" in query_lower:
            intent["analytical_methods"].append("anomaly_detection")

        # Output requirements
        if any(word in query_lower for word in ["visualize", "chart", "graph", "plot"]):
            intent["output_requirements"].append("visualization")
        if any(word in query_lower for word in ["table", "list", "breakdown"]):
            intent["output_requirements"].append("tabular_data")
        if any(word in query_lower for word in ["report", "summary", "narrative"]):
            intent["output_requirements"].append("narrative_summary")

        return intent

    def _initialize_sector_mapping(self) -> Dict[str, List[str]]:
        """Initialize sector keyword mappings"""
        return {
            "Education": ["education", "school", "learning", "literacy", "university", "training"],
            "Health": ["health", "medical", "hospital", "healthcare", "medicine", "clinic"],
            "Infrastructure": ["infrastructure", "transport", "roads", "bridges", "utilities", "energy"],
            "Agriculture": ["agriculture", "farming", "rural", "food security", "irrigation"],
            "Water": ["water", "sanitation", "sewage", "drainage", "hygiene"],
            "Energy": ["energy", "power", "electricity", "renewable", "solar", "wind"],
            "Climate": ["climate", "environment", "carbon", "emissions", "adaptation", "mitigation"],
            "Governance": ["governance", "institution", "public sector", "transparency", "accountability"],
            "Financial Sector": ["financial", "banking", "capital markets", "insurance", "fintech"],
            "Social Protection": ["social protection", "safety net", "pension", "unemployment", "welfare"]
        }

    def _initialize_financial_indicators(self) -> Dict[str, List[str]]:
        """Initialize financial indicator patterns"""
        return {
            "commitment": ["commitment", "committed", "approved", "allocated"],
            "disbursement": ["disbursement", "disbursed", "paid out", "transferred"],
            "expenditure": ["expenditure", "spent", "expense", "outflow"],
            "efficiency": ["efficiency", "ratio", "utilization", "performance"],
            "leverage": ["leverage", "multiplier", "co-financing", "mobilization"]
        }

    def _initialize_geographic_mapping(self) -> Dict[str, List[str]]:
        """Initialize geographic entity mappings"""
        return {
            "region": [
                "Sub-Saharan Africa", "East Asia and Pacific", "Europe and Central Asia",
                "Latin America and Caribbean", "Middle East and North Africa", "South Asia"
            ],
            "country": [
                "India", "Nigeria", "Bangladesh", "Indonesia", "Pakistan", "Kenya",
                "Ethiopia", "Tanzania", "Uganda", "Ghana", "Vietnam", "Philippines"
            ]
        }

    def _initialize_temporal_patterns(self) -> Dict[str, str]:
        """Initialize temporal pattern recognition"""
        return {
            r"last (\d+) years?": "years_back",
            r"since (\d{4})": "since_year",
            r"(\d{4})-(\d{4})": "year_range",
            r"fy\s*(\d{4})": "fiscal_year",
            r"q[1-4]\s+(\d{4})": "quarter_year"
        }

class TrendAnalyzer:
    """Advanced trend analysis with statistical rigor"""

    def __init__(self):
        self.significance_threshold = 0.05
        self.trend_window_min = 12  # Minimum data points for trend analysis

    def analyze_portfolio_trends(self, data: pd.DataFrame, metric: str) -> TrendAnalysis:
        """Comprehensive trend analysis of portfolio metrics"""

        if len(data) < self.trend_window_min:
            return self._insufficient_data_result()

        # Calculate trend components
        trend_direction = self._calculate_trend_direction(data, metric)
        trend_strength = self._calculate_trend_strength(data, metric)
        seasonal_patterns = self._detect_seasonal_patterns(data, metric)
        breakpoints = self._detect_structural_breaks(data, metric)
        forecast = self._generate_forecast(data, metric)

        # Statistical significance testing
        trend_significance = self._test_trend_significance(data, metric)

        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            seasonal_patterns=seasonal_patterns,
            breakpoints=breakpoints,
            forecast=forecast,
            trend_significance=trend_significance
        )

    def _calculate_trend_direction(self, data: pd.DataFrame, metric: str) -> str:
        """Calculate overall trend direction using multiple methods"""

        values = data[metric].values
        time_index = np.arange(len(values))

        # Linear regression slope
        slope = np.polyfit(time_index, values, 1)[0]

        # Mann-Kendall trend test for robustness
        mk_stat, mk_p_value = self._mann_kendall_test(values)

        # Determine direction
        if abs(slope) < 0.001 and mk_p_value > 0.05:
            return "stable"
        elif slope > 0 and mk_stat > 0:
            return "increasing"
        elif slope < 0 and mk_stat < 0:
            return "decreasing"
        else:
            return "volatile"

    def _calculate_trend_strength(self, data: pd.DataFrame, metric: str) -> float:
        """Calculate trend strength (0-1 scale)"""

        values = data[metric].values
        time_index = np.arange(len(values))

        # R-squared from linear regression
        coeffs = np.polyfit(time_index, values, 1)
        y_pred = np.polyval(coeffs, time_index)
        r_squared = 1 - (np.sum((values - y_pred) ** 2) / np.sum((values - np.mean(values)) ** 2))

        return max(0, min(1, r_squared))

    def _detect_seasonal_patterns(self, data: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """Detect seasonal patterns in the data"""

        if 'date' not in data.columns:
            return {"seasonal": False, "patterns": []}

        data['month'] = pd.to_datetime(data['date']).dt.month
        data['quarter'] = pd.to_datetime(data['date']).dt.quarter

        monthly_avg = data.groupby('month')[metric].mean()
        quarterly_avg = data.groupby('quarter')[metric].mean()

        # Test for seasonal significance
        monthly_cv = monthly_avg.std() / monthly_avg.mean()
        quarterly_cv = quarterly_avg.std() / quarterly_avg.mean()

        patterns = []
        if monthly_cv > 0.1:  # 10% coefficient of variation threshold
            patterns.append({
                "type": "monthly",
                "strength": monthly_cv,
                "peak_months": monthly_avg.nlargest(3).index.tolist(),
                "low_months": monthly_avg.nsmallest(3).index.tolist()
            })

        if quarterly_cv > 0.1:
            patterns.append({
                "type": "quarterly",
                "strength": quarterly_cv,
                "peak_quarters": quarterly_avg.nlargest(2).index.tolist(),
                "low_quarters": quarterly_avg.nsmallest(2).index.tolist()
            })

        return {
            "seasonal": len(patterns) > 0,
            "patterns": patterns
        }

    def _mann_kendall_test(self, data: np.ndarray) -> Tuple[float, float]:
        """Implement Mann-Kendall trend test"""

        n = len(data)
        s = 0

        for i in range(n - 1):
            for j in range(i + 1, n):
                if data[j] > data[i]:
                    s += 1
                elif data[j] < data[i]:
                    s -= 1

        var_s = (n * (n - 1) * (2 * n + 5)) / 18

        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0

        # Two-tailed test
        p_value = 2 * (1 - self._standard_normal_cdf(abs(z)))

        return s, p_value

    def _standard_normal_cdf(self, x: float) -> float:
        """Standard normal CDF approximation"""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))

class AnomalyDetector:
    """Detect anomalies in portfolio data using statistical methods"""

    def __init__(self):
        self.methods = ["statistical_outliers", "isolation_forest", "time_series_anomalies"]

    def detect_portfolio_anomalies(self, data: pd.DataFrame, metrics: List[str]) -> Dict[str, Any]:
        """Comprehensive anomaly detection across multiple metrics"""

        anomalies = {
            "statistical_outliers": {},
            "temporal_anomalies": {},
            "multivariate_anomalies": {},
            "summary": {}
        }

        for metric in metrics:
            if metric in data.columns:
                # Statistical outliers
                anomalies["statistical_outliers"][metric] = self._detect_statistical_outliers(
                    data, metric
                )

                # Temporal anomalies (if time series data)
                if 'date' in data.columns:
                    anomalies["temporal_anomalies"][metric] = self._detect_temporal_anomalies(
                        data, metric
                    )

        # Multivariate anomalies
        if len(metrics) > 1:
            numeric_cols = [col for col in metrics if col in data.columns]
            if len(numeric_cols) > 1:
                anomalies["multivariate_anomalies"] = self._detect_multivariate_anomalies(
                    data[numeric_cols]
                )

        # Summary statistics
        total_anomalies = sum(
            len(anomalies["statistical_outliers"].get(metric, [])) for metric in metrics
        )
        anomalies["summary"] = {
            "total_anomalies": total_anomalies,
            "anomaly_rate": total_anomalies / len(data) if len(data) > 0 else 0,
            "metrics_affected": len([m for m in metrics if m in anomalies["statistical_outliers"]])
        }

        return anomalies

    def _detect_statistical_outliers(self, data: pd.DataFrame, metric: str) -> List[Dict[str, Any]]:
        """Detect statistical outliers using IQR and z-score methods"""

        values = data[metric].dropna()
        outliers = []

        # IQR method
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        iqr_outliers = data[(data[metric] < lower_bound) | (data[metric] > upper_bound)]

        # Z-score method
        z_scores = np.abs((values - values.mean()) / values.std())
        z_outliers = data[z_scores > 3]

        # Combine and deduplicate
        all_outlier_indices = set(iqr_outliers.index) | set(z_outliers.index)

        for idx in all_outlier_indices:
            outlier_value = data.loc[idx, metric]
            outliers.append({
                "index": idx,
                "value": outlier_value,
                "z_score": abs((outlier_value - values.mean()) / values.std()),
                "iqr_bounds": [lower_bound, upper_bound],
                "severity": "extreme" if abs((outlier_value - values.mean()) / values.std()) > 4 else "moderate"
            })

        return outliers

class InsightGenerator:
    """Generate executive-level insights from analytical results"""

    def __init__(self):
        self.insight_templates = self._initialize_insight_templates()

    def generate_comprehensive_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive insights from multiple analytical results"""

        insights = []

        # Financial insights
        if "financial_analysis" in analysis_results:
            insights.extend(self._generate_financial_insights(analysis_results["financial_analysis"]))

        # Performance insights
        if "performance_analysis" in analysis_results:
            insights.extend(self._generate_performance_insights(analysis_results["performance_analysis"]))

        # Trend insights
        if "trend_analysis" in analysis_results:
            insights.extend(self._generate_trend_insights(analysis_results["trend_analysis"]))

        # Risk insights
        if "anomaly_detection" in analysis_results:
            insights.extend(self._generate_risk_insights(analysis_results["anomaly_detection"]))

        # Prioritize and rank insights
        insights = self._prioritize_insights(insights)

        return insights[:10]  # Return top 10 insights

    def _generate_financial_insights(self, financial_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate financial performance insights"""

        insights = []

        # Disbursement efficiency insight
        if "disbursement_ratio" in financial_data:
            ratio = financial_data["disbursement_ratio"]
            if ratio > 0.85:
                insights.append({
                    "type": "financial_performance",
                    "priority": "high",
                    "title": "Exceptional Disbursement Performance",
                    "finding": f"Portfolio demonstrates {ratio:.1%} disbursement efficiency",
                    "impact": "Strong project implementation and financial management",
                    "recommendation": "Share best practices across regions and sectors",
                    "confidence": 0.95
                })
            elif ratio < 0.60:
                insights.append({
                    "type": "financial_concern",
                    "priority": "high",
                    "title": "Disbursement Efficiency Below Target",
                    "finding": f"Portfolio disbursement rate at {ratio:.1%}",
                    "impact": "Potential implementation delays affecting development outcomes",
                    "recommendation": "Conduct detailed review of implementation bottlenecks",
                    "confidence": 0.90
                })

        # Portfolio concentration insight
        if "sector_concentration" in financial_data:
            concentration = financial_data["sector_concentration"]
            if max(concentration.values()) > 0.4:
                top_sector = max(concentration, key=concentration.get)
                insights.append({
                    "type": "portfolio_risk",
                    "priority": "medium",
                    "title": "High Sector Concentration Risk",
                    "finding": f"{top_sector} represents {concentration[top_sector]:.1%} of portfolio",
                    "impact": "Concentration risk may limit portfolio resilience",
                    "recommendation": "Consider diversification opportunities in other sectors",
                    "confidence": 0.85
                })

        return insights

    def _prioritize_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize insights based on importance and actionability"""

        priority_weights = {"high": 3, "medium": 2, "low": 1}

        for insight in insights:
            score = 0
            score += priority_weights.get(insight.get("priority", "low"), 1) * 10
            score += insight.get("confidence", 0.5) * 5
            score += len(insight.get("recommendation", "")) / 100  # Actionability proxy

            insight["priority_score"] = score

        return sorted(insights, key=lambda x: x["priority_score"], reverse=True)

    def _initialize_insight_templates(self) -> Dict[str, str]:
        """Initialize insight templates for consistent formatting"""
        return {
            "financial": "## 💰 {title}\n\n**Finding**: {finding}\n**Impact**: {impact}\n**Action**: {recommendation}",
            "performance": "## 📊 {title}\n\n**Analysis**: {finding}\n**Implication**: {impact}\n**Next Steps**: {recommendation}",
            "risk": "## ⚠️ {title}\n\n**Risk Identified**: {finding}\n**Potential Impact**: {impact}\n**Mitigation**: {recommendation}"
        }

# Example usage and testing
def demonstrate_analytics():
    """Demonstrate advanced analytics capabilities"""

    print("🔍 World Bank IATI Advanced Analytics Demo")
    print("="*50)

    # Initialize components
    query_processor = AdvancedQueryProcessor()
    trend_analyzer = TrendAnalyzer()
    anomaly_detector = AnomalyDetector()
    insight_generator = InsightGenerator()

    # Sample complex query
    sample_query = "Analyze education sector disbursement trends in Sub-Saharan Africa over the last 5 years, comparing performance against infrastructure investments and identifying any anomalies or risks"

    print(f"\n📝 Sample Query: {sample_query}")

    # Process query
    parsed_query = query_processor.parse_complex_query(sample_query)
    print(f"\n🎯 Query Classification: {parsed_query['query_type']}")
    print(f"🔍 Entities Identified: {len(parsed_query['entities']['sectors'])} sectors, {len(parsed_query['entities']['regions'])} regions")
    print(f"🧠 Analytical Intent: {parsed_query['intent']['primary_objective']}")
    print(f"⚙️ Required Methods: {', '.join(parsed_query['intent']['analytical_methods'])}")

    # Generate sample data for demonstration
    dates = pd.date_range('2019-01-01', '2024-12-31', freq='Q')
    sample_data = pd.DataFrame({
        'date': dates,
        'education_commitment': np.random.normal(2.5, 0.5, len(dates)) * 1e9,
        'education_disbursement': np.random.normal(1.8, 0.4, len(dates)) * 1e9,
        'infrastructure_commitment': np.random.normal(4.2, 0.8, len(dates)) * 1e9,
        'infrastructure_disbursement': np.random.normal(3.1, 0.6, len(dates)) * 1e9
    })

    # Add some realistic trends and anomalies
    sample_data['education_commitment'] *= (1 + np.arange(len(dates)) * 0.02)  # Growth trend
    sample_data.loc[15, 'education_disbursement'] *= 0.3  # Anomaly

    print(f"\n📊 Sample Data Generated: {len(sample_data)} quarterly observations")

    # Trend analysis
    education_trend = trend_analyzer.analyze_portfolio_trends(sample_data, 'education_commitment')
    print(f"\n📈 Education Trend: {education_trend.trend_direction} (strength: {education_trend.trend_strength:.2f})")

    # Anomaly detection
    anomalies = anomaly_detector.detect_portfolio_anomalies(
        sample_data, ['education_disbursement', 'infrastructure_disbursement']
    )
    print(f"\n🚨 Anomalies Detected: {anomalies['summary']['total_anomalies']} across {anomalies['summary']['metrics_affected']} metrics")

    # Generate insights
    analysis_results = {
        "financial_analysis": {
            "disbursement_ratio": 0.72,
            "sector_concentration": {"Education": 0.35, "Infrastructure": 0.28, "Health": 0.20, "Other": 0.17}
        },
        "trend_analysis": education_trend,
        "anomaly_detection": anomalies
    }

    insights = insight_generator.generate_comprehensive_insights(analysis_results)
    print(f"\n💡 Generated Insights: {len(insights)} executive-level findings")

    for i, insight in enumerate(insights[:3], 1):
        print(f"\n{i}. {insight['title']}")
        print(f"   Priority: {insight['priority']} | Confidence: {insight['confidence']:.1%}")

    print("\n✅ Advanced Analytics Demonstration Complete")

if __name__ == "__main__":
    demonstrate_analytics()