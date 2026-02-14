"""
DigitalOcean Agent Endpoint Integration (Streamlit Cloud-ready)

Fixes:
- Uses correct DigitalOcean Agent endpoint path: {AGENT_ENDPOINT}/api/v1/chat/completions
- OpenAI-compatible payload: {"messages":[...], "stream": false, ...}
- Optional retrieval/functions/guardrails info (for real grounded data + citations)
- Robust JSON extraction from agent responses
- Graceful handling of 404s / schema drift
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from wb_iati_agent_config import AgentConfig

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ----------------------------
# Data structures
# ----------------------------
@dataclass
class APIResponse:
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


# ----------------------------
# Helpers
# ----------------------------
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"(\{(?:[^{}]|(?R))*\})", re.DOTALL)  # recursive-ish best effort


def _safe_json_loads(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        return None


def _extract_json_from_text(text: str) -> Optional[dict]:
    """
    Tries, in order:
    1) fenced ```json {..}```
    2) first valid JSON object substring
    3) direct json.loads(text)
    """
    if not text:
        return None

    m = _JSON_FENCE_RE.search(text)
    if m:
        obj = _safe_json_loads(m.group(1))
        if obj is not None:
            return obj

    # try direct
    obj = _safe_json_loads(text.strip())
    if obj is not None:
        return obj

    # try substring extraction
    for m2 in _JSON_OBJECT_RE.finditer(text):
        cand = m2.group(1)
        obj = _safe_json_loads(cand)
        if obj is not None:
            return obj

    return None


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = (endpoint or "").strip().rstrip("/")
    return endpoint


# ----------------------------
# Core client
# ----------------------------
class DigitalOceanAgentClient:
    """
    Calls a deployed DO Agent endpoint (agents.do-ai.run) using the documented schema.
    Docs: {AGENT_ENDPOINT}/docs
    Chat endpoint: POST {AGENT_ENDPOINT}/api/v1/chat/completions
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.endpoint = _normalize_endpoint(config.endpoint)
        self.access_key = (config.api_key or "").strip()
        self.timeout_s = 60

        if not self.endpoint:
            raise ValueError("Missing agent endpoint (config.endpoint).")
        if not self.access_key:
            raise ValueError("Missing agent access key (config.api_key).")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_key}",
                "Content-Type": "application/json",
                "User-Agent": f"WB-IATI-Agent/{config.version}",
            }
        )

        logger.info(
            "DigitalOceanAgentClient initialized (endpoint=%s, version=%s)",
            self.endpoint,
            config.version,
        )

    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        *,
        include_retrieval_info: bool = True,
        include_functions_info: bool = True,
        include_guardrails_info: bool = True,
        stream: bool = False,
        max_retries: int = 3,
    ) -> APIResponse:
        """
        POST {endpoint}/api/v1/chat/completions
        OpenAI-compatible response with optional "retrieval" object.
        """
        url = f"{self.endpoint}/api/v1/chat/completions"

        payload = {
            "messages": messages,
            "stream": stream,
            "include_retrieval_info": include_retrieval_info,
            "include_functions_info": include_functions_info,
            "include_guardrails_info": include_guardrails_info,
        }

        start = time.time()
        last_err = None

        for attempt in range(1, max_retries + 1):
            try:
                r = self.session.post(url, json=payload, timeout=self.timeout_s)
                dt = time.time() - start

                # Non-retryable (4xx except 429)
                if 400 <= r.status_code < 500 and r.status_code != 429:
                    logger.error("Non-retryable response %s for POST %s: %s", r.status_code, url, r.text[:500])
                    return APIResponse(
                        success=False,
                        status_code=r.status_code,
                        error=r.text,
                        execution_time=dt,
                    )

                if r.status_code == 200:
                    try:
                        data = r.json()
                    except Exception:
                        data = {"raw_text": r.text}
                    return APIResponse(success=True, status_code=200, data=data, execution_time=dt)

                # Retryable
                last_err = f"HTTP {r.status_code}: {r.text[:300]}"
                time.sleep(min(2 ** (attempt - 1), 8))

            except Exception as e:
                last_err = str(e)
                time.sleep(min(2 ** (attempt - 1), 8))

        dt = time.time() - start
        logger.error("Request failed after %s attempts: POST %s -> %s", max_retries, url, last_err)
        return APIResponse(success=False, status_code=0, error=last_err, execution_time=dt)

    def quick_test(self) -> Dict[str, Any]:
        """
        Light connectivity test.
        """
        resp = self.chat_completions(
            [{"role": "user", "content": "Reply with: OK"}],
            include_retrieval_info=False,
            include_functions_info=False,
            include_guardrails_info=False,
            max_retries=2,
        )
        if not resp.success:
            return {"overall_status": "failed", "error": resp.error, "status_code": resp.status_code}
        return {"overall_status": "passed", "status_code": 200}


# ----------------------------
# High-level interface used by app
# ----------------------------
class ChatbotInterface:
    """
    Provides app-friendly methods:
    - send_iati_query(): returns parsed JSON if agent returned it
    - create_dashboard_request(): structured metrics for charts
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = DigitalOceanAgentClient(config)

    def initialize_session(self) -> bool:
        # Nothing to persist server-side; keep for compatibility
        return True

    def send_iati_query(
        self,
        query: str,
        *,
        mode: str = "analysis",
        force_json: bool = True,
        include_retrieval_info: bool = True,
    ) -> Dict[str, Any]:
        """
        Sends a user query to the DO agent and attempts to parse structured JSON.
        """
        system_prompt = (
            "You are a World Bank IATI Intelligence Agent. "
            "Prioritize grounded answers from the connected knowledge base. "
        )

        json_instruction = (
            "Return a SINGLE JSON object (no markdown) using this schema:\n"
            "{\n"
            '  "executive_summary": "string",\n'
            '  "key_metrics": [{"label":"string","value":number,"unit":"string","note":"string"}],\n'
            '  "charts": [\n'
            "     {\n"
            '       "title":"string",\n'
            '       "type":"bar|line|pie|heatmap|scatter",\n'
            '       "x_label":"string",\n'
            '       "y_label":"string",\n'
            '       "data": [{"x":"string","y":number,"series":"string"}]\n'
            "     }\n"
            "  ],\n"
            '  "risks": [{"risk":"string","severity":"Low|Moderate|High","evidence":"string"}],\n'
            '  "recommendations": ["string"],\n'
            '  "data_confidence": 0.0,\n'
            '  "notes": "string"\n'
            "}\n"
            "If some numeric fields are not available from grounded sources, omit them or leave them null—do NOT fabricate."
        )

        messages = [{"role": "system", "content": system_prompt + (json_instruction if force_json else "")}]
        messages.append({"role": "user", "content": query})

        resp = self.client.chat_completions(
            messages,
            include_retrieval_info=include_retrieval_info,
            include_functions_info=True,
            include_guardrails_info=True,
            stream=False,
        )

        if not resp.success:
            return {
                "ok": False,
                "error": resp.error,
                "status_code": resp.status_code,
                "raw": resp.data,
            }

        data = resp.data or {}
        content = ""
        try:
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")  # OpenAI-style
        except Exception:
            content = ""

        parsed = _extract_json_from_text(content) if force_json else None

        return {
            "ok": True,
            "response_text": content,
            "parsed": parsed,
            "retrieval": data.get("retrieval"),
            "guardrails": data.get("guardrails"),
            "functions": data.get("functions"),
            "raw": data,
        }

    def create_dashboard_request(self, dashboard_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses the agent to produce dashboard-ready structured output.
        """
        prompt = (
            f"Create a {dashboard_type} portfolio dashboard using grounded IATI data where available. "
            f"Parameters: {json.dumps(params)}. "
            "Return JSON using the schema previously specified."
        )
        return self.send_iati_query(prompt, mode="dashboard", force_json=True, include_retrieval_info=True)


def test_connection(config: AgentConfig) -> Dict[str, Any]:
    """
    Compatibility shim used by older orchestrator code.
    """
    try:
        client = DigitalOceanAgentClient(config)
        return client.quick_test()
    except Exception as e:
        return {"overall_status": "failed", "error": str(e), "status_code": 0}
