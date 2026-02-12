"""
Dashboard Framework for World Bank IATI Intelligence Agent
Enterprise-grade dashboard generation and visualization components
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
import numpy as np

@dataclass
class VisualizationComponent:
    """Standard visualization component structure"""
    component_id: str
    type: str  # chart_type: bar, line, pie, heatmap, map, etc.
    title: str
    data_source: str
    configuration: Dict[str, Any]
    size: str = "medium"  # small, medium, large, full-width
    priority: int = 1  # 1=high, 2=medium, 3=low
    interactive: bool = True
    export_enabled: bool = True

@dataclass
class DashboardLayout:
    """Dashboard layout and configuration"""
    dashboard_id: str
    title: str
    description: str
    components: List[VisualizationComponent]
    filters: List[Dict[str, Any]]
    layout_type: str = "grid"  # grid, tabs, accordion
    refresh_interval: int = 300  # seconds
    permissions: List[str] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["world_bank_staff", "management", "board"]

class ExecutiveDashboardBuilder:
    """Builder for executive-level dashboards with KPIs and strategic insights"""

    @staticmethod
    def create_portfolio_overview() -> DashboardLayout:
        """Create comprehensive portfolio overview dashboard"""

        components = [
            # KPI Cards Row
            VisualizationComponent(
                component_id="total_commitment_kpi",
                type="kpi_card",
                title="Total Commitments",
                data_source="portfolio_summary",
                size="small",
                priority=1,
                configuration={
                    "metric": "total_commitment_usd",
                    "format": "currency_billions",
                    "comparison": "vs_last_year",
                    "trend_indicator": True,
                    "color_scheme": "wb_blue"
                }
            ),

            VisualizationComponent(
                component_id="disbursement_ratio_kpi",
                type="kpi_card",
                title="Disbursement Efficiency",
                data_source="portfolio_summary",
                size="small",
                priority=1,
                configuration={
                    "metric": "disbursement_ratio",
                    "format": "percentage",
                    "target": 0.75,
                    "threshold": {"good": 0.8, "warning": 0.6},
                    "color_scheme": "performance"
                }
            ),

            VisualizationComponent(
                component_id="active_projects_kpi",
                type="kpi_card",
                title="Active Projects",
                data_source="project_count",
                size="small",
                priority=1,
                configuration={
                    "metric": "active_project_count",
                    "format": "integer",
                    "trend_period": "quarterly",
                    "breakdown_available": True
                }
            ),

            VisualizationComponent(
                component_id="countries_served_kpi",
                type="kpi_card",
                title="Countries Served",
                data_source="geographic_summary",
                size="small",
                priority=1,
                configuration={
                    "metric": "unique_countries",
                    "format": "integer",
                    "additional_info": "regions_count",
                    "drill_down": "country_list"
                }
            ),

            # Main Visualizations Row
            VisualizationComponent(
                component_id="sector_portfolio_pie",
                type="pie_chart",
                title="Portfolio Distribution by Sector",
                data_source="sector_aggregation",
                size="medium",
                priority=1,
                configuration={
                    "group_by": "sector_name",
                    "value": "commitment_usd",
                    "show_percentages": True,
                    "max_slices": 8,
                    "others_category": True,
                    "hover_details": ["project_count", "disbursement_ratio"],
                    "color_palette": "wb_sectors"
                }
            ),

            VisualizationComponent(
                component_id="disbursement_trends",
                type="line_chart",
                title="Quarterly Disbursement Trends",
                data_source="quarterly_financial_data",
                size="medium",
                priority=1,
                configuration={
                    "x_axis": "quarter",
                    "y_axis": ["commitment_usd", "disbursement_usd"],
                    "time_range": "last_24_months",
                    "dual_axis": True,
                    "annotations": ["major_events", "policy_changes"],
                    "forecast": {"enabled": True, "periods": 4}
                }
            ),

            # Geographic Visualization
            VisualizationComponent(
                component_id="global_portfolio_map",
                type="choropleth_map",
                title="Global Portfolio Distribution",
                data_source="country_portfolio_summary",
                size="large",
                priority=2,
                configuration={
                    "color_metric": "total_commitment_usd",
                    "size_metric": "project_count",
                    "color_scale": "sequential_blues",
                    "zoom_enabled": True,
                    "tooltip": [
                        "country_name", "commitment_usd", "disbursement_usd",
                        "project_count", "primary_sectors"
                    ],
                    "click_action": "drill_down_country"
                }
            ),

            # Performance Analysis
            VisualizationComponent(
                component_id="top_countries_performance",
                type="horizontal_bar_chart",
                title="Top 15 Countries by Portfolio Size",
                data_source="country_rankings",
                size="medium",
                priority=2,
                configuration={
                    "y_axis": "country_name",
                    "x_axis": "total_commitment_usd",
                    "color_by": "disbursement_ratio",
                    "sort": "descending",
                    "limit": 15,
                    "bar_labels": True,
                    "color_scale": "diverging_rd_yl_bu"
                }
            ),

            # Risk and Performance Indicators
            VisualizationComponent(
                component_id="portfolio_risk_matrix",
                type="scatter_plot",
                title="Portfolio Risk vs Performance Matrix",
                data_source="risk_performance_analysis",
                size="medium",
                priority=2,
                configuration={
                    "x_axis": "portfolio_risk_score",
                    "y_axis": "disbursement_efficiency",
                    "size": "commitment_usd",
                    "color": "region",
                    "quadrants": {
                        "labels": ["Low Risk/High Perf", "High Risk/High Perf",
                                 "Low Risk/Low Perf", "High Risk/Low Perf"],
                        "thresholds": {"risk": 0.5, "performance": 0.75}
                    },
                    "tooltip": ["country_name", "sector_concentration", "avg_project_size"]
                }
            )
        ]

        filters = [
            {
                "filter_id": "date_range",
                "type": "date_range_picker",
                "label": "Time Period",
                "default": "last_12_months",
                "options": ["last_6_months", "last_12_months", "last_24_months", "custom"]
            },
            {
                "filter_id": "sector_filter",
                "type": "multi_select",
                "label": "Sectors",
                "data_source": "sector_list",
                "default": "all",
                "search_enabled": True
            },
            {
                "filter_id": "region_filter",
                "type": "dropdown",
                "label": "Region",
                "data_source": "region_list",
                "default": "all_regions",
                "include_all_option": True
            },
            {
                "filter_id": "instrument_filter",
                "type": "checkbox_group",
                "label": "Financing Instruments",
                "options": ["IDA", "IBRD", "Trust Funds", "Grants"],
                "default": ["IDA", "IBRD"]
            }
        ]

        return DashboardLayout(
            dashboard_id="wb_executive_overview_v2",
            title="World Bank Portfolio Executive Dashboard",
            description="Comprehensive overview of World Bank development finance portfolio with key performance indicators and strategic insights",
            components=components,
            filters=filters,
            layout_type="grid",
            refresh_interval=300
        )

class SectorDashboardBuilder:
    """Builder for sector-specific deep-dive dashboards"""

    @staticmethod
    def create_sector_analysis(sector: str = None) -> DashboardLayout:
        """Create sector-specific analysis dashboard"""

        sector_title = f"{sector} Sector" if sector else "Sector"

        components = [
            # Sector Overview KPIs
            VisualizationComponent(
                component_id="sector_commitment_total",
                type="kpi_card",
                title=f"{sector_title} Total Commitment",
                data_source="sector_financial_summary",
                size="small",
                priority=1,
                configuration={
                    "metric": "sector_commitment_usd",
                    "format": "currency_billions",
                    "sector_filter": sector,
                    "comparison": "vs_portfolio_average"
                }
            ),

            # Sector Timeline Analysis
            VisualizationComponent(
                component_id="sector_commitment_timeline",
                type="area_chart",
                title=f"{sector_title} Commitment Timeline",
                data_source="sector_time_series",
                size="large",
                priority=1,
                configuration={
                    "x_axis": "approval_date",
                    "y_axis": "cumulative_commitment",
                    "fill_area": True,
                    "annotations": ["major_initiatives", "policy_changes"],
                    "time_range": "last_60_months"
                }
            ),

            # Geographic Distribution
            VisualizationComponent(
                component_id="sector_geographic_heatmap",
                type="heatmap",
                title=f"{sector_title} Investment by Country-Year",
                data_source="sector_country_matrix",
                size="large",
                priority=1,
                configuration={
                    "x_axis": "fiscal_year",
                    "y_axis": "country_name",
                    "value": "commitment_usd",
                    "color_scale": "sequential_oranges",
                    "cell_labels": True,
                    "sort_y": "total_commitment_desc"
                }
            ),

            # Sub-sector Breakdown
            VisualizationComponent(
                component_id="subsector_waterfall",
                type="waterfall_chart",
                title=f"{sector_title} Sub-sector Breakdown",
                data_source="subsector_analysis",
                size="medium",
                priority=2,
                configuration={
                    "categories": "subsector_name",
                    "values": "commitment_usd",
                    "show_total": True,
                    "color_positive": "wb_blue",
                    "color_negative": "wb_red"
                }
            ),

            # Results and Impact
            VisualizationComponent(
                component_id="sector_results_scorecard",
                type="scorecard",
                title=f"{sector_title} Results Achievement",
                data_source="sector_results_framework",
                size="medium",
                priority=2,
                configuration={
                    "metrics": [
                        {"name": "Output Indicators", "actual": "outputs_achieved", "target": "outputs_target"},
                        {"name": "Outcome Indicators", "actual": "outcomes_achieved", "target": "outcomes_target"},
                        {"name": "Impact Indicators", "actual": "impacts_achieved", "target": "impacts_target"}
                    ],
                    "color_scheme": "traffic_light",
                    "show_progress_bars": True
                }
            ),

            # Implementation Partners
            VisualizationComponent(
                component_id="sector_partner_network",
                type="network_diagram",
                title=f"{sector_title} Implementation Partners",
                data_source="sector_partner_mapping",
                size="large",
                priority=3,
                configuration={
                    "node_size": "partnership_value",
                    "edge_width": "collaboration_strength",
                    "node_color": "partner_type",
                    "layout": "force_directed",
                    "interactive": True,
                    "show_labels": True
                }
            )
        ]

        return DashboardLayout(
            dashboard_id=f"wb_sector_{sector.lower().replace(' ', '_')}_analysis" if sector else "wb_sector_analysis",
            title=f"World Bank {sector_title} Analysis Dashboard",
            description=f"Deep-dive analysis of World Bank {sector.lower()} sector investments, performance, and impact",
            components=components,
            filters=[],
            layout_type="tabs"
        )

class CountryDashboardBuilder:
    """Builder for country-specific portfolio dashboards"""

    @staticmethod
    def create_country_portfolio(country: str = None) -> DashboardLayout:
        """Create country-specific portfolio dashboard"""

        country_title = country if country else "Country"

        components = [
            # Country Portfolio Overview
            VisualizationComponent(
                component_id="country_portfolio_summary",
                type="metric_grid",
                title=f"{country_title} Portfolio Summary",
                data_source="country_portfolio_data",
                size="full-width",
                priority=1,
                configuration={
                    "metrics": [
                        {"label": "Total Commitment", "value": "total_commitment", "format": "currency"},
                        {"label": "Total Disbursed", "value": "total_disbursed", "format": "currency"},
                        {"label": "Active Projects", "value": "active_projects", "format": "integer"},
                        {"label": "Disbursement Rate", "value": "disbursement_rate", "format": "percentage"},
                        {"label": "Avg Project Size", "value": "avg_project_size", "format": "currency"},
                        {"label": "Implementation Period", "value": "avg_duration", "format": "years"}
                    ],
                    "layout": "2x3_grid"
                }
            ),

            # Project List with Status
            VisualizationComponent(
                component_id="country_project_list",
                type="data_table",
                title=f"Active Projects in {country_title}",
                data_source="country_active_projects",
                size="large",
                priority=1,
                configuration={
                    "columns": [
                        {"field": "project_name", "title": "Project", "width": 200, "sortable": True},
                        {"field": "sector", "title": "Sector", "width": 120, "filterable": True},
                        {"field": "commitment_usd", "title": "Commitment", "format": "currency", "width": 120},
                        {"field": "disbursed_usd", "title": "Disbursed", "format": "currency", "width": 120},
                        {"field": "disbursement_ratio", "title": "Disb. Rate", "format": "percentage", "width": 100},
                        {"field": "status", "title": "Status", "width": 100, "color_coded": True},
                        {"field": "closing_date", "title": "Closing", "format": "date", "width": 100}
                    ],
                    "pagination": True,
                    "export_enabled": True,
                    "row_click_action": "project_detail"
                }
            ),

            # Financial Flow Analysis
            VisualizationComponent(
                component_id="country_financial_waterfall",
                type="waterfall_chart",
                title=f"{country_title} Financial Flow Analysis",
                data_source="country_financial_flow",
                size="medium",
                priority=1,
                configuration={
                    "start_value": "commitment_amount",
                    "end_value": "disbursed_amount",
                    "intermediate_steps": ["cancelled", "restructured", "additional_financing"],
                    "color_scheme": "wb_financial"
                }
            ),

            # Sector Composition
            VisualizationComponent(
                component_id="country_sector_donut",
                type="donut_chart",
                title=f"{country_title} Portfolio by Sector",
                data_source="country_sector_breakdown",
                size="medium",
                priority=2,
                configuration={
                    "inner_radius": 0.5,
                    "show_labels": True,
                    "show_percentages": True,
                    "sort": "descending",
                    "color_palette": "wb_sectors"
                }
            ),

            # Implementation Timeline
            VisualizationComponent(
                component_id="country_project_timeline",
                type="gantt_chart",
                title=f"{country_title} Project Timeline",
                data_source="country_project_schedule",
                size="large",
                priority=2,
                configuration={
                    "task_field": "project_name",
                    "start_field": "approval_date",
                    "end_field": "closing_date",
                    "progress_field": "completion_percentage",
                    "color_field": "sector",
                    "milestone_events": ["mid_term_review", "implementation_completion"],
                    "zoom_levels": ["month", "quarter", "year"]
                }
            ),

            # Results Framework Progress
            VisualizationComponent(
                component_id="country_results_dashboard",
                type="results_scorecard",
                title=f"{country_title} Development Results",
                data_source="country_results_data",
                size="large",
                priority=2,
                configuration={
                    "result_categories": ["PDO", "Intermediate Outcomes", "Outputs"],
                    "achievement_levels": ["achieved", "mostly_achieved", "partially_achieved", "not_achieved"],
                    "show_trend": True,
                    "traffic_light_indicators": True
                }
            )
        ]

        return DashboardLayout(
            dashboard_id=f"wb_country_{country.lower().replace(' ', '_')}_portfolio" if country else "wb_country_portfolio",
            title=f"World Bank Portfolio in {country_title}",
            description=f"Comprehensive analysis of World Bank development finance portfolio and results in {country}",
            components=components,
            filters=[],
            layout_type="accordion"
        )

class ThematicDashboardBuilder:
    """Builder for thematic dashboards (Climate, Gender, Fragility, etc.)"""

    @staticmethod
    def create_climate_dashboard() -> DashboardLayout:
        """Create climate finance dashboard"""

        components = [
            # Climate Finance Overview
            VisualizationComponent(
                component_id="climate_finance_kpis",
                type="kpi_row",
                title="Climate Finance Overview",
                data_source="climate_finance_summary",
                size="full-width",
                priority=1,
                configuration={
                    "kpis": [
                        {"title": "Climate Co-benefits", "value": "climate_cobenefits_usd", "format": "currency_billions"},
                        {"title": "Adaptation Share", "value": "adaptation_percentage", "format": "percentage"},
                        {"title": "Mitigation Share", "value": "mitigation_percentage", "format": "percentage"},
                        {"title": "Climate Projects", "value": "climate_project_count", "format": "integer"}
                    ]
                }
            ),

            # Climate Investment by Region
            VisualizationComponent(
                component_id="climate_regional_comparison",
                type="stacked_bar_chart",
                title="Climate Investment by Region",
                data_source="climate_regional_data",
                size="large",
                priority=1,
                configuration={
                    "x_axis": "region",
                    "y_axis": "investment_usd",
                    "stack_by": "climate_theme",
                    "stack_categories": ["Adaptation", "Mitigation", "Cross-cutting"],
                    "show_totals": True,
                    "color_palette": "climate_themes"
                }
            ),

            # Climate Risk vs Investment
            VisualizationComponent(
                component_id="climate_risk_investment_scatter",
                type="bubble_chart",
                title="Climate Risk vs Investment Intensity",
                data_source="climate_risk_analysis",
                size="large",
                priority=1,
                configuration={
                    "x_axis": "climate_risk_index",
                    "y_axis": "climate_investment_per_capita",
                    "bubble_size": "total_population",
                    "color": "income_group",
                    "regression_line": True,
                    "tooltip": ["country", "climate_vulnerability", "adaptation_priority"]
                }
            ),

            # SDG Alignment Matrix
            VisualizationComponent(
                component_id="climate_sdg_matrix",
                type="matrix_heatmap",
                title="Climate Projects - SDG Alignment",
                data_source="climate_sdg_mapping",
                size="medium",
                priority=2,
                configuration={
                    "x_axis": "sdg_goal",
                    "y_axis": "climate_theme",
                    "cell_value": "project_count",
                    "cell_color": "investment_intensity",
                    "show_values": True
                }
            )
        ]

        return DashboardLayout(
            dashboard_id="wb_climate_finance_dashboard",
            title="World Bank Climate Finance Dashboard",
            description="Analysis of World Bank climate finance investments, co-benefits, and alignment with climate goals",
            components=components,
            filters=[],
            layout_type="grid"
        )

class DashboardExporter:
    """Export dashboards to various formats"""

    @staticmethod
    def export_to_json(dashboard: DashboardLayout) -> str:
        """Export dashboard configuration to JSON"""
        dashboard_dict = asdict(dashboard)
        return json.dumps(dashboard_dict, indent=2, default=str)

    @staticmethod
    def export_to_powerbi(dashboard: DashboardLayout) -> Dict[str, Any]:
        """Export dashboard configuration for Power BI"""

        powerbi_config = {
            "name": dashboard.title,
            "description": dashboard.description,
            "pages": [],
            "dataModels": [],
            "relationships": []
        }

        # Convert components to Power BI visuals
        for component in dashboard.components:
            powerbi_visual = {
                "name": component.title,
                "type": DashboardExporter._map_chart_type_powerbi(component.type),
                "position": {"x": 0, "y": 0, "width": 6, "height": 4},  # Default positioning
                "config": component.configuration,
                "dataBinding": {
                    "dataSource": component.data_source,
                    "fields": DashboardExporter._extract_fields(component.configuration)
                }
            }
            powerbi_config["pages"].append(powerbi_visual)

        return powerbi_config

    @staticmethod
    def export_to_tableau(dashboard: DashboardLayout) -> Dict[str, Any]:
        """Export dashboard configuration for Tableau"""

        tableau_config = {
            "workbook": {
                "name": dashboard.title,
                "description": dashboard.description,
                "dashboards": [{
                    "name": dashboard.title,
                    "worksheets": []
                }]
            }
        }

        for component in dashboard.components:
            worksheet = {
                "name": component.title,
                "mark": DashboardExporter._map_chart_type_tableau(component.type),
                "encoding": DashboardExporter._map_encoding_tableau(component.configuration),
                "data": {"source": component.data_source}
            }
            tableau_config["workbook"]["dashboards"][0]["worksheets"].append(worksheet)

        return tableau_config

    @staticmethod
    def _map_chart_type_powerbi(chart_type: str) -> str:
        """Map internal chart types to Power BI visual types"""
        mapping = {
            "bar_chart": "clusteredBarChart",
            "line_chart": "lineChart",
            "pie_chart": "pieChart",
            "scatter_plot": "scatterChart",
            "heatmap": "matrix",
            "kpi_card": "card",
            "choropleth_map": "filledMap"
        }
        return mapping.get(chart_type, "table")

    @staticmethod
    def _map_chart_type_tableau(chart_type: str) -> str:
        """Map internal chart types to Tableau mark types"""
        mapping = {
            "bar_chart": "bar",
            "line_chart": "line",
            "pie_chart": "pie",
            "scatter_plot": "circle",
            "heatmap": "square",
            "choropleth_map": "map"
        }
        return mapping.get(chart_type, "text")

    @staticmethod
    def _extract_fields(configuration: Dict[str, Any]) -> List[str]:
        """Extract field names from configuration"""
        fields = []

        for key, value in configuration.items():
            if key in ["x_axis", "y_axis", "group_by", "color_by", "size", "metric"]:
                if isinstance(value, str):
                    fields.append(value)
                elif isinstance(value, list):
                    fields.extend(value)

        return fields

    @staticmethod
    def _map_encoding_tableau(configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Map configuration to Tableau encoding"""
        encoding = {}

        if "x_axis" in configuration:
            encoding["x"] = {"field": configuration["x_axis"], "type": "ordinal"}
        if "y_axis" in configuration:
            encoding["y"] = {"field": configuration["y_axis"], "type": "quantitative"}
        if "color_by" in configuration:
            encoding["color"] = {"field": configuration["color_by"], "type": "nominal"}
        if "size" in configuration:
            encoding["size"] = {"field": configuration["size"], "type": "quantitative"}

        return encoding

# Usage example and testing
def create_sample_dashboards() -> Dict[str, DashboardLayout]:
    """Create sample dashboards for testing and demonstration"""

    dashboards = {
        "executive": ExecutiveDashboardBuilder.create_portfolio_overview(),
        "education_sector": SectorDashboardBuilder.create_sector_analysis("Education"),
        "india_country": CountryDashboardBuilder.create_country_portfolio("India"),
        "climate_thematic": ThematicDashboardBuilder.create_climate_dashboard()
    }

    return dashboards

if __name__ == "__main__":
    # Generate sample dashboards
    sample_dashboards = create_sample_dashboards()

    print("🎯 Dashboard Framework Initialized")
    print(f"📊 Generated {len(sample_dashboards)} sample dashboards:")

    for name, dashboard in sample_dashboards.items():
        print(f"  - {name}: {len(dashboard.components)} components")

        # Export to JSON for review
        json_export = DashboardExporter.export_to_json(dashboard)
        print(f"    JSON config: {len(json_export)} characters")

    print("\n✅ Dashboard framework ready for integration")