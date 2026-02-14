# do_api_integration.py
"""
DigitalOcean Gradient AI Agents integration (OpenAI-compatible)

Fixes:
- Uses the correct Agent endpoint path:  /api/v1/chat/completions
- Parses standard chat.completion schema: choices[0].message.content
- Optional inclusion of retrieval/guardrails/functions info (if supported by your agent endpoint)
- Uses synchronous requests to avoid Streamlit event loop issues
- Provides a clean, stable APIResponse object + helper extraction of JSON metrics blocks

Expected Streamlit secrets / env vars:
- DO_ENDPOINT   (e.g. https://xxxx.agents.do-ai.run)
- DO_API_KEY    (Agent access key)
- DO_CHATBOT_ID (optional; retained for backward-compat; not required by /chat/completions)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# -----------------------------
# Data structures
# -----------------------------
@dataclass
class APIResponse:
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    text: str = ""
    error: Optional[str] = None
    execution_time: Optional[float] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status_code": self.status_code,
            "data": self.data,
            "text": self.text,
            "error": self.error,
            "execution_time": self.execution_time,
            "url": self.url,
        }


# -----------------------------
# Helpers
# -----------------------------
def _safe_json_loads(s: str) -> Optional[Any]:
    try:
        return json.loads(s)
    except Exception:
        return None


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from:
    - a ```json fenced block
    - or the first parseable {...} object
    """
    if not text:
        return None

    # Prefer fenced json blocks
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        obj = _safe_json_loads(m.group(1))
        if isinstance(obj, dict):
            return obj

    # Fallback: first parseable object-like chunk
    candidates = re.findall(r"\{(?:[^{}]|(?R))*\}", text, flags=re.DOTALL)
    for c in candidates:
        obj = _safe_json_loads(c)
        if isinstance(obj, dict):
            return obj
    return None


def build_messages(user_prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": user_prompt})
    return msgs


# -----------------------------
# DigitalOcean Agent client (OpenAI-compatible)
# -----------------------------
class DigitalOceanAgentClient:
    """
    Calls a DigitalOcean Gradient AI Agent endpoint using OpenAI-compatible Chat Completions.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        timeout_s: int = 45,
        default_model: Optional[str] = None,
        chatbot_id: Optional[str] = None,  # retained for older codepaths (not required)
    ):
        if not endpoint:
            raise ValueError("endpoint is required")

        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key or ""
        self.timeout_s = timeout_s
        self.default_model = default_model
        self.chatbot_id = chatbot_id

        self.chat_url = f"{self.endpoint}/api/v1/chat/completions"

        logger.info(
            "DigitalOceanAgentClient initialized (chat_url=%s, chatbot_id=%s)",
            self.chat_url,
            self.chatbot_id,
        )

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        stream: bool = False,
        include_retrieval_info: bool = True,
        include_functions_info: bool = False,
        include_guardrails_info: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """
        Returns APIResponse where:
        - data is the full JSON response from DO
        - text is best-effort extracted assistant content (choices[0].message.content)
        """
        payload: Dict[str, Any] = {
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # DO docs mention these toggles; if unsupported, server may ignore or reject.
            "include_retrieval_info": include_retrieval_info,
            "include_functions_info": include_functions_info,
            "include_guardrails_info": include_guardrails_info,
        }
        if model or self.default_model:
            payload["model"] = model or self.default_model

        # Backward-compat: some older stacks used chatbot_id in payload
        if self.chatbot_id:
            payload["chatbot_id"] = self.chatbot_id

        if extra:
            payload.update(extra)

        t0 = time.time()
        try:
            r = requests.post(self.chat_url, headers=self._headers(), json=payload, timeout=self.timeout_s)
            dt = time.time() - t0

            raw_text = r.text or ""
            data = None
            try:
                data = r.json()
            except Exception:
                data = None

            if not (200 <= r.status_code < 300):
                logger.error("Non-retryable response %s for POST %s: %s", r.status_code, self.chat_url, raw_text[:400])
                return APIResponse(
                    success=False,
                    status_code=r.status_code,
                    data=data if isinstance(data, dict) else None,
                    text="",
                    error=raw_text[:600] or "Request failed",
                    execution_time=dt,
                    url=self.chat_url,
                )

            # Extract assistant message content
            assistant_text = ""
            if isinstance(data, dict):
                try:
                    assistant_text = data["choices"][0]["message"]["content"]
                except Exception:
                    assistant_text = raw_text

            return APIResponse(
                success=True,
                status_code=r.status_code,
                data=data if isinstance(data, dict) else None,
                text=assistant_text or raw_text,
                error=None,
                execution_time=dt,
                url=self.chat_url,
            )

        except Exception as e:
            dt = time.time() - t0
            logger.exception("Request failed: POST %s -> %s", self.chat_url, str(e))
            return APIResponse(
                success=False,
                status_code=-1,
                data=None,
                text="",
                error=str(e),
                execution_time=dt,
                url=self.chat_url,
            )


# -----------------------------
# Compatibility wrapper used by orchestrator / Streamlit
# -----------------------------
class ChatbotInterface:
    """
    Backward-compatible interface expected by main_agent_orchestrator,
    but powered by DigitalOceanAgentClient using /api/v1/chat/completions.
    """

    def __init__(self, config: Any):
        self.endpoint = getattr(config, "endpoint", None) or os.environ.get("DO_ENDPOINT", "")
        self.api_key = getattr(config, "api_key", None) or os.environ.get("DO_API_KEY", "")
        self.chatbot_id = getattr(config, "chatbot_id", None) or os.environ.get("DO_CHATBOT_ID", None)

        self.client = DigitalOceanAgentClient(
            endpoint=self.endpoint,
            api_key=self.api_key,
            chatbot_id=self.chatbot_id,
        )

    async def health_check(self) -> APIResponse:
        # No dedicated health endpoint guaranteed; do a tiny completion
        msgs = build_messages("ping", system_prompt="Reply with 'pong'.")
        return self.client.chat_completions(msgs, max_tokens=20, include_retrieval_info=False)

    async def get_agent_capabilities(self) -> APIResponse:
        # Not standardized; keep non-fatal in orchestrator
        msgs = build_messages(
            "List your capabilities as JSON with keys: tools, data_sources, limitations.",
            system_prompt="Return only JSON.",
        )
        return self.client.chat_completions(msgs, max_tokens=250, include_retrieval_info=False)

    async def send_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        Main method for chat. Encourage the agent to return a JSON metrics block when possible.
        """
        sys = (
            "You are an executive analytics agent for World Bank IATI portfolio intelligence. "
            "When possible, include a ```json metrics``` block with structured fields:\n"
            "{\n"
            '  "regional_investment_by_sector": [{"Category": "...", "Value": number}],\n'
            '  "active_projects_global": [{"Region": "...", "ActiveProjects": number, "AvgCommitmentUSDm": number}],\n'
            '  "portfolio_trend": [{"Year": number, "InvestmentBn": number, "DisbursementBn": number}],\n'
            '  "risk_heatmap": [{"RiskLevel":"Low|Moderate|High", "Africa": number, "Asia": number, "Europe": number, "MENA": number, "Americas": number}],\n'
            '  "kpis": {"budget_utilized_pct": number, "impact_score": number, "risk_exposure": "Low|Moderate|High"}\n'
            "}\n"
            "If you cannot provide numbers, explain what is missing and still provide best-effort estimates labeled as estimates."
        )
        user = query
        if context:
            user += "\n\nContext:\n" + json.dumps(context)[:4000]

        msgs = build_messages(user, system_prompt=sys)
        return self.client.chat_completions(
            msgs,
            temperature=0.2,
            max_tokens=1400,
            include_retrieval_info=True,
            include_guardrails_info=False,
            include_functions_info=False,
        )


# Convenience (kept for older imports)
async def test_connection(config: Any) -> Dict[str, Any]:
    ci = ChatbotInterface(config)
    resp = await ci.health_check()
    return {
        "overall_status": "passed" if resp.success else "failed",
        "status_code": resp.status_code,
        "error": resp.error,
        "url": resp.url,
    }
