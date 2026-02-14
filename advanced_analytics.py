# advanced_analytics.py
"""
Advanced Analytics Module for World Bank IATI Intelligence Agent
Provides advanced query parsing, entity extraction, trend/anomaly hooks, and insight scaffolding.

This file is Streamlit-safe (no asyncio.run).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


class AdvancedQueryProcessor:
    """
    Parses complex natural language queries and extracts entities, intent, and analysis needs.
    """

    def __init__(self):
        # Lightweight lexicons — extend as needed
        self.dashboard_keywords = {
            "dashboard", "scorecard", "kpi", "metrics", "visualize", "visualisation",
            "chart", "charts", "report", "executive dashboard"
        }

        self.trend_keywords = {"trend", "trends", "over time", "trajectory", "growth", "decline"}
        self.anomaly_keywords = {"anomaly", "outlier", "unusual", "spike", "unexpected", "irregular"}

        # Minimal sector & region hints (optional)
        self.sector_keywords = {
            "health", "education", "infrastructure", "energy", "transport", "water",
            "agriculture", "finance", "governance", "climate"
        }

        # You can expand this list as you wish
        self.common_countries = {
            "ethiopia", "kenya", "nigeria", "india", "pakistan", "bangladesh",
            "tanzania", "uganda", "ghana", "south africa"
        }

    def parse_complex_query(self, query: str) -> Dict[str, Any]:
        """
        Main entrypoint used by orchestrator.
        Returns: dict with query_type, entities, intent, and optional metadata.
        """
        query = query or ""
        q_lower = query.lower().strip()

        query_type = self._classify_query_type(q_lower)

        return {
            "query_type": query_type,
            "entities": self._extract_entities_advanced(q_lower),
            "intent": self._extract_intent(q_lower),
            "metadata": {
                "length": len(query),
            }
        }

    # -----------------------------
    # Query classification
    # -----------------------------
    def _classify_query_type(self, q_lower: str) -> str:
        if any(k in q_lower for k in self.dashboard_keywords):
            return "dashboard_request"
        return "analysis"

    # -----------------------------
    # Intent extraction
    # -----------------------------
    def _extract_intent(self, q_lower: str) -> Dict[str, Any]:
        analytical_methods: List[str] = []
        if any(k in q_lower for k in self.trend_keywords):
            analytical_methods.append("trend")
        if any(k in q_lower for k in self.anomaly_keywords):
            analytical_methods.append("anomaly_detection")

        return {
            "analytical_methods": analytical_methods,
            "wants_summary": ("summary" in q_lower) or ("executive" in q_lower),
        }

    # -----------------------------
    # Entity extraction
    # -----------------------------
    def _extract_entities_advanced(self, q_lower: str) -> Dict[str, Any]:
        sectors = self._extract_sectors(q_lower)
        countries = self._extract_countries(q_lower)

        time_matches = self._extract_temporal_entities(q_lower)  # ✅ FIXED

        return {
            "sectors": sectors,
            "countries": countries,
            "temporal": time_matches.get("temporal_entities", []),
        }

    def _extract_sectors(self, q_lower: str) -> List[str]:
        found = []
        for s in self.sector_keywords:
            if re.search(rf"\b{re.escape(s)}\b", q_lower):
                found.append(s.title())
        return found

    def _extract_countries(self, q_lower: str) -> List[str]:
        found = []
        # Match from known list
        for c in self.common_countries:
            if re.search(rf"\b{re.escape(c)}\b", q_lower):
                found.append(c.title())
        # Also match patterns like "in Kenya", "for Ethiopia"
        # (lightweight heuristic)
        pattern = re.compile(r"\b(?:in|for|across|within)\s+([a-z][a-z\s\-]{2,40})\b")
        for m in pattern.finditer(q_lower):
            candidate = m.group(1).strip()
            # stop at common trailing words
            candidate = re.split(r"\b(by|with|and|or|over|during|since|from|to)\b", candidate)[0].strip()
            # reject if obviously not a country phrase
            if len(candidate) < 3:
                continue
            # Title-case candidate
            cand_title = " ".join([w.capitalize() for w in candidate.split()])
            # Avoid duplicates; keep small
            if cand_title not in found and len(found) < 5:
                found.append(cand_title)
        return found

    # -----------------------------
    # ✅ Missing method: temporal entity extraction
    # -----------------------------
    def _extract_temporal_entities(self, text: str) -> Dict[str, Any]:
        """
        Extracts basic temporal entities:
        - explicit years (e.g., 2021)
        - year ranges (e.g., 2019-2021, 2019 to 2021)
        - relative periods (e.g., last 3 years, last quarter)
        Returns: {"temporal_entities":[...]}
        """
        if not text:
            return {"temporal_entities": []}

        entities: List[Dict[str, Any]] = []

        # Year range patterns: 2019-2021, 2019 to 2021, 2019–2021
        range_pattern = re.compile(r"\b((?:19|20)\d{2})\s*(?:-|–|to|through)\s*((?:19|20)\d{2})\b", re.IGNORECASE)
        for m in range_pattern.finditer(text):
            entities.append({
                "type": "year_range",
                "start": m.group(1),
                "end": m.group(2),
                "text": m.group(0)
            })

        # Standalone years: 1990-2099 (filter out those already in ranges)
        years_in_ranges = set()
        for e in entities:
            if e.get("type") == "year_range":
                years_in_ranges.add(e.get("start"))
                years_in_ranges.add(e.get("end"))

        year_pattern = re.compile(r"\b((?:19|20)\d{2})\b")
        for m in year_pattern.finditer(text):
            y = m.group(1)
            if y in years_in_ranges:
                continue
            entities.append({"type": "year", "value": y, "text": y})

        # Relative periods: last X years/months/weeks/days
        rel_pattern = re.compile(r"\b(last|past)\s+(\d+)\s+(years?|months?|weeks?|days?)\b", re.IGNORECASE)
        for m in rel_pattern.finditer(text):
            entities.append({
                "type": "relative_period",
                "direction": "past",
                "value": int(m.group(2)),
                "unit": m.group(3).lower(),
                "text": m.group(0)
            })

        # Named relative periods
        named = {
            "last year": ("past", 1, "year"),
            "last quarter": ("past", 1, "quarter"),
            "last month": ("past", 1, "month"),
            "last week": ("past", 1, "week"),
            "this year": ("current", 1, "year"),
            "this quarter": ("current", 1, "quarter"),
            "this month": ("current", 1, "month"),
        }
        for phrase, (mode, v, unit) in named.items():
            if phrase in text:
                entities.append({
                    "type": "relative_named",
                    "mode": mode,
                    "value": v,
                    "unit": unit,
                    "text": phrase
                })

        return {"temporal_entities": entities}


# --- Optional scaffolding classes your orchestrator imports ---
# Keep these minimal so imports don't fail even if you don't use them yet.

class TrendAnalyzer:
    pass

class AnomalyDetector:
    pass

class InsightGenerator:
    pass
