# World Bank IATI Intelligence Agent

**Enterprise-grade AI system for International Aid Transparency Initiative (IATI) data analysis and insights**

## 🌍 Overview

The World Bank IATI Intelligence Agent is an advanced AI system designed to democratize access to development finance data, enabling stakeholders to understand aid flows, project effectiveness, and development impact through natural language interaction and intelligent visualization.

### Key Features

- **🤖 Natural Language Processing**: Ask questions in plain English about World Bank portfolio data
- **📊 Executive Dashboards**: Generate board-level dashboards with KPIs and strategic insights
- **📈 Advanced Analytics**: Trend analysis, anomaly detection, and predictive modeling
- **🔍 Multi-dimensional Analysis**: Financial flows, sector performance, geographic distribution, results framework
- **⚡ Real-time Integration**: Connected to Digital Ocean knowledge source for enhanced insights
- **📋 Multiple Export Formats**: JSON, Power BI, Tableau, Excel compatibility

## 🏗️ Architecture

### Core Components

1. **Agent Orchestrator** (`main_agent_orchestrator.py`)
   - Central coordination layer
   - Query routing and response synthesis
   - Performance monitoring and session management

2. **Intelligence Agent** (`wb_iati_intelligence_agent.py`)
   - Core analytical engine
   - Natural language query processing
   - Insight generation and recommendation engine

3. **Digital Ocean Integration** (`do_api_integration.py`)
   - API connectivity to knowledge source
   - Enhanced query processing with external data
   - Rate limiting and error handling

4. **Dashboard Framework** (`dashboard_framework.py`)
   - Executive, sector, country, and thematic dashboards
   - Multiple visualization types and export formats
   - Responsive and interactive components

5. **Advanced Analytics** (`advanced_analytics.py`)
   - Trend analysis and forecasting
   - Statistical anomaly detection
   - Comparative and performance analytics

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Digital Ocean API access (configured)
- World Bank IATI data access

### Installation

1. **Clone and setup environment:**
```bash
cd "WBG IATI Data Intelligence Agent"
pip install -r requirements.txt
```

2. **Configure API credentials:**
```python
# API credentials will be prompted on first use
# Or set via environment variables:
API_KEY = "YOUR_DIGITAL_OCEAN_API_KEY"
ENDPOINT = "https://your-agent-endpoint.agents.do-ai.run"
CHATBOT_ID = "YOUR_CHATBOT_ID"
```

3. **Initialize and test:**
```bash
python main_agent_orchestrator.py
```

## 📈 Usage Examples

### Basic Query Processing

```python
from main_agent_orchestrator import WBIATIAgentOrchestrator

# Initialize agent
orchestrator = WBIATIAgentOrchestrator()
await orchestrator.initialize()

# Process natural language queries
result = await orchestrator.process_user_query(
    "How much has the World Bank committed to climate projects in Africa since 2020?"
)

print(f"Summary: {result['executive_summary']}")
print(f"Insights: {len(result['key_insights'])} findings")
```

### Dashboard Creation

```python
# Create executive dashboard
dashboard = await orchestrator.create_executive_dashboard("executive")
print(f"Dashboard created: {dashboard['dashboard_id']}")

# Create sector-specific dashboard
sector_dashboard = await orchestrator.create_executive_dashboard(
    "sector",
    {"sector": "Education"}
)
```

### Advanced Analytics

```python
from advanced_analytics import AdvancedQueryProcessor, TrendAnalyzer

# Process complex queries
processor = AdvancedQueryProcessor()
parsed = processor.parse_complex_query(
    "Analyze education disbursement trends and identify performance anomalies"
)

# Generate trend analysis
analyzer = TrendAnalyzer()
trends = analyzer.analyze_portfolio_trends(data, 'disbursement_amount')
print(f"Trend direction: {trends.trend_direction}")
```

## 🎯 Query Examples

The agent can process sophisticated natural language queries:

### Financial Analysis
- *"What is the World Bank's total active portfolio by region?"*
- *"Show me disbursement efficiency trends over the last 5 years"*
- *"Compare IDA versus IBRD financing patterns in South Asia"*

### Sector Performance
- *"Analyze education sector performance in fragile and conflict-affected states"*
- *"What are the top performing infrastructure projects by disbursement rate?"*
- *"Show me climate co-benefits across all World Bank investments"*

### Geographic Insights
- *"Which countries have the highest concentration of World Bank projects?"*
- *"Compare regional portfolio performance metrics"*
- *"Map sub-national distribution of health sector investments in Nigeria"*

### Executive Dashboards
- *"Create an executive dashboard showing FY2024 portfolio performance"*
- *"Generate a climate finance dashboard with SDG alignment"*
- *"Build a country portfolio analysis for India with risk indicators"*

## 📊 Dashboard Types

### 1. Executive Overview Dashboard
- **Purpose**: Board-level portfolio monitoring
- **Components**: KPI cards, sector distribution, disbursement trends, global map, risk matrix
- **Audience**: Senior management, Board of Directors
- **Refresh**: Real-time

### 2. Sector Deep-Dive Dashboard
- **Purpose**: Sector-specific performance analysis
- **Components**: Timeline analysis, geographic heatmaps, partner networks, results scorecards
- **Audience**: Sector managers, technical specialists
- **Refresh**: Daily

### 3. Country Portfolio Dashboard
- **Purpose**: Country-level portfolio management
- **Components**: Project listings, financial flows, implementation timelines, results framework
- **Audience**: Country directors, project teams
- **Refresh**: Daily

### 4. Thematic Dashboard (Climate, Gender, etc.)
- **Purpose**: Cross-cutting theme analysis
- **Components**: Investment tracking, SDG alignment, impact metrics, regional comparisons
- **Audience**: Thematic specialists, policy teams
- **Refresh**: Weekly

## 🔧 Configuration

### Agent Configuration (`wb_iati_agent_config.py`)

```python
@dataclass
class AgentConfig:
    api_key: str = "3vgEVfMeM5_rggpNoeLpe0agHBAN42yD"
    endpoint: str = "https://mrngtcmmhzbbdopptwzoirop.agents.do-ai.run"
    chatbot_id: str = "1FV8wQ78ZHOndsmrfmaNXmjpxi-snRAW"
    data_coverage: str = "$50B+ annual commitments"
    countries_covered: int = 170
```

### Dashboard Templates
- Configurable layouts and components
- Multiple visualization types
- Export to Power BI, Tableau, Excel
- Mobile-responsive design

### Analytics Settings
- Confidence thresholds for insights
- Trend analysis parameters
- Anomaly detection sensitivity
- Forecasting horizons

## 🔍 Advanced Features

### 1. Multi-Dimensional Analysis
- **Cross-tabulation**: Analyze data across multiple dimensions simultaneously
- **Drill-down capabilities**: Navigate from high-level overviews to detailed project data
- **Dynamic filtering**: Real-time data slicing and filtering

### 2. Predictive Analytics
- **Disbursement forecasting**: Predict future disbursement patterns
- **Risk modeling**: Identify projects at risk of implementation delays
- **Portfolio optimization**: Recommend portfolio rebalancing strategies

### 3. Natural Language Insights
- **Executive summaries**: Auto-generated narrative insights
- **Contextual recommendations**: Actionable next steps based on analysis
- **Stakeholder-specific formatting**: Tailored outputs for different audiences

## 🛡️ Data Quality and Validation

### Data Quality Framework
- **Completeness checks**: Validate data coverage and missing values
- **Consistency validation**: Ensure data integrity across sources
- **Freshness monitoring**: Track data update recency
- **Confidence scoring**: Assign confidence levels to all analyses

### Quality Indicators
```python
DATA_QUALITY_INDICATORS = {
    "completeness": {"threshold": 0.95, "warning": "Data gaps identified"},
    "freshness": {"max_age_days": 30, "warning": "Data may be outdated"},
    "consistency": {"variance_threshold": 0.1, "warning": "Inconsistencies detected"}
}
```

## 📈 Performance Monitoring

### Key Metrics
- **Query Response Time**: Target <3 seconds for standard queries
- **Dashboard Generation**: Target <10 seconds for complex dashboards
- **API Reliability**: 99.9% uptime target
- **Data Freshness**: Updated within 24 hours of source updates

### Session Tracking
```python
session_stats = {
    "queries_processed": 0,
    "dashboards_created": 0,
    "insights_generated": 0,
    "avg_response_time": 0.0,
    "session_start": datetime.now()
}
```

## 🔄 API Integration

### Digital Ocean Endpoint
- **Endpoint**: `https://mrngtcmmhzbbdopptwzoirop.agents.do-ai.run`
- **Authentication**: Bearer token authentication
- **Rate Limits**: 60 requests per minute
- **Response Format**: JSON with structured data and metadata

### Integration Methods
1. **Synchronous Queries**: Standard request-response pattern
2. **Streaming Responses**: Real-time updates for long-running analyses
3. **Batch Processing**: Multiple queries in single request
4. **Webhook Support**: Event-driven notifications

## 🧪 Testing and Validation

### Unit Tests
```bash
pytest tests/ -v
```

### Integration Tests
```bash
python -m pytest tests/integration/ -v
```

### Load Testing
```bash
python tests/load_test.py
```

## 🚀 Deployment

### Production Checklist
- [ ] API credentials configured
- [ ] Data sources connected and validated
- [ ] Dashboard templates tested
- [ ] Analytics pipeline validated
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] Documentation updated

### Scaling Considerations
- **Horizontal scaling**: Multiple agent instances behind load balancer
- **Caching layer**: Redis for frequently accessed data
- **Database optimization**: Connection pooling and query optimization
- **Monitoring**: Comprehensive logging and alerting

## 📚 Documentation

### Architecture Documents
- System architecture overview
- Component interaction diagrams
- Data flow documentation
- Security and compliance guidelines

### User Guides
- Executive user manual
- Analyst workflow guide
- Dashboard customization guide
- Query optimization tips

### Technical References
- API reference documentation
- Configuration parameter guide
- Troubleshooting handbook
- Extension development guide

## 🔧 Support and Maintenance

### Monitoring and Alerts
- **Health checks**: Automated system health monitoring
- **Performance alerts**: Response time and error rate monitoring
- **Data quality alerts**: Automatic data quality issue detection
- **Usage analytics**: Query patterns and user behavior tracking

### Maintenance Schedule
- **Daily**: Data refresh and quality checks
- **Weekly**: Performance optimization and capacity planning
- **Monthly**: Security updates and dependency upgrades
- **Quarterly**: Major feature releases and system updates

## 🤝 Contributing

This is an enterprise system developed for the World Bank. For questions, support requests, or enhancement proposals, please contact the development team.

### Code Standards
- Python 3.8+ with type hints
- Black code formatting
- Comprehensive docstrings
- Unit test coverage >90%
- Security-first development practices

---

**World Bank IATI Intelligence Agent v1.0.0**
*Democratizing access to development finance data through AI-powered insights*

🌍 **Empowering evidence-based development finance decisions across 170+ countries**