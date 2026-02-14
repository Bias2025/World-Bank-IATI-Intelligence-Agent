# do_api_integration.py
"""
Async DigitalOcean / Agent API client for the WB IATI Intelligence Agent.
- Uses aiohttp for non-blocking requests
- Reuses a single ClientSession per client instance
- Implements timeouts, retries with exponential backoff + jitter, and simple token-bucket rate limiting
- Returns APIResponse dataclass instances for consistent handling by orchestrator
"""

from __future__ import annotations
import asyncio
import aiohttp
import logging
import time
import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

# Import your project's AgentConfig (adjust if named differently)
try:
    from wb_iati_agent_config import AgentConfig
except Exception:
    # Provide a minimal fallback so the file is importable for tests. Replace in production with your real config class.
    @dataclass
    class AgentConfig:
        api_key: Optional[str] = None
        endpoint: Optional[str] = None
        chatbot_id: Optional[str] = None
        version: str = "1.0.0"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class APIResponse:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    execution_time: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RateLimiter:
    """
    Simple token-bucket rate limiter.
    capacity: max tokens
    refill_rate: tokens per second
    """

    def __init__(self, capacity: int = 60, refill_rate_per_minute: int = 60):
        self.capacity = capacity
        self.tokens = capacity
        # refill_rate_per_minute -> tokens per second
        self.refill_rate = refill_rate_per_minute / 60.0
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self._last = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class DigitalOceanAPI:
    """
    Async client to interact with the agent endpoint (DigitalOcean or other agent endpoint).
    Use .initialize() to warm up the session if desired.
    """

    DEFAULT_TIMEOUT = 30  # seconds for general requests
    HEALTH_TIMEOUT = 8

    def __init__(self, config: AgentConfig, *, max_retries: int = 3, backoff_base: float = 0.5):
        self.config = config
        self.base_url = (config.endpoint or "").rstrip("/")
        self.api_key = getattr(config, "api_key", None)
        self.chatbot_id = getattr(config, "chatbot_id", None)
        self.version = getattr(config, "version", "1.0.0")
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        self._is_closed = False

        # Retry and backoff params
        self.max_retries = max_retries
        self.backoff_base = backoff_base

        # Rate limiter (default 60 req/minute capacity)
        self.rate_limiter = RateLimiter(capacity=120, refill_rate_per_minute=120)

        logger.info("DigitalOceanAPI client initialized (endpoint=%s, chatbot_id=%s)", self.base_url, self.chatbot_id)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        async with self._session_lock:
            if self._session and not self._session.closed:
                return self._session
            timeout = aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT)
            headers = {
                "User-Agent": f"WB-IATI-Agent/{self.version}",
                "Accept": "application/json",
            }
            # Authorization header set per-request to avoid caching credentials accidentally
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
            return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        self._is_closed = True

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _default_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.chatbot_id:
            headers["X-Chatbot-ID"] = str(self.chatbot_id)
        return headers

    async def _request_with_retries(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> APIResponse:
        """
        Internal generic request wrapper with retries, timeouts, and rate limiting.
        """
        if self._is_closed:
            return APIResponse(success=False, error="Client closed", status_code=None)

        if not await self.rate_limiter.allow_request():
            logger.warning("Rate limiter blocking request to %s %s", method, path)
            return APIResponse(success=False, error="Rate limit exceeded", status_code=429)

        session = await self._ensure_session()
        url = f"{self.base_url}{path}"

        headers = await self._default_headers()

        attempt = 0
        start_time = time.time()
        last_exception = None

        # Use provided timeout or fallback to default
        timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT

        while attempt <= self.max_retries:
            attempt += 1
            try:
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with session.request(method, url, params=params, json=json_payload, headers=headers, timeout=timeout) as resp:
                    exec_time = time.time() - start_time
                    status = resp.status
                    text = await resp.text()
                    # Try to parse json when possible
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        data = None

                    if 200 <= status < 300:
                        return APIResponse(success=True, data=data or text, status_code=status, execution_time=exec_time)
                    # handle retryable status codes: 429, 502-504, 500
                    if status in (429, 500, 502, 503, 504):
                        # raise to be caught by retry logic below
                        last_exception = Exception(f"Transient HTTP {status}: {text}")
                        logger.warning("Transient error on attempt %s for %s %s: %s", attempt, method, url, status)
                        # fall through to retry/backoff
                    else:
                        # non-retryable client error — return immediately
                        logger.error("Non-retryable response %s for %s %s: %s", status, method, url, text)
                        return APIResponse(success=False, error=text, status_code=status, execution_time=exec_time, data=data)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_exception = e
                logger.exception("Request exception on attempt %s for %s %s: %s", attempt, method, url, e)

            # If we are here, we will retry (unless attempts exhausted)
            if attempt > self.max_retries:
                break
            # Exponential backoff with jitter
            backoff = (2 ** (attempt - 1)) * self.backoff_base
            jitter = random.uniform(0, backoff * 0.25)
            sleep_for = backoff + jitter
            logger.info("Retrying in %.2fs (attempt %d of %d) for %s %s", sleep_for, attempt, self.max_retries, method, url)
            await asyncio.sleep(sleep_for)

        total_time = time.time() - start_time
        err_text = str(last_exception) if last_exception else "Unknown error"
        logger.error("Request failed after %d attempts: %s %s -> %s", attempt, method, url, err_text)
        return APIResponse(success=False, error=err_text, status_code=getattr(last_exception, "status", None), execution_time=total_time)

    # Public API: health check
    async def health_check(self) -> APIResponse:
        """
        GET /health
        """
        if not self.base_url:
            return APIResponse(success=False, error="No endpoint configured")
        return await self._request_with_retries("GET", "/health", timeout_seconds=self.HEALTH_TIMEOUT)

    async def get_agent_capabilities(self) -> APIResponse:
        """
        GET /capabilities
        """
        if not self.base_url:
            return APIResponse(success=False, error="No endpoint configured")
        return await self._request_with_retries("GET", "/capabilities", timeout_seconds=15)

    async def send_query(self, query: str, context: Optional[Dict[str, Any]] = None, *, session_id: Optional[str] = None) -> APIResponse:
        """
        POST /chat
        payload includes: query, chatbot_id, context, timestamp, session_id
        """
        if not self.base_url:
            return APIResponse(success=False, error="No endpoint configured")
        payload = {
            "query": query,
            "chatbot_id": self.chatbot_id,
            "context": context or {},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": session_id or f"wb_iati_{int(time.time())}"
        }
        return await self._request_with_retries("POST", "/chat", json_payload=payload, timeout_seconds=self.DEFAULT_TIMEOUT)

    # Convenience synchronous wrappers (only for short-lived sync code that needs them)
    def health_check_sync(self, timeout: int = 8) -> APIResponse:
        return asyncio.run(self.health_check())

    def send_query_sync(self, query: str, context: Optional[Dict[str, Any]] = None) -> APIResponse:
        return asyncio.run(self.send_query(query, context))

    # Helper to ensure graceful cleanup if the program exits
    def __del__(self):
        if self._session and not self._session.closed:
            # best-effort cleanup; can't await here
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # schedule close
                    asyncio.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception:
                # last resort: ignore
                pass


# If executed directly, run a tiny smoke test (requires environment / config)
if __name__ == "__main__":
    import os, asyncio
    logging.getLogger().setLevel(logging.DEBUG)
    cfg = AgentConfig(
        api_key=os.environ.get("DO_API_KEY"),
        endpoint=os.environ.get("DO_ENDPOINT"),
        chatbot_id=os.environ.get("DO_CHATBOT_ID"),
    )
    client = DigitalOceanAPI(cfg)
    async def smoke():
        print("Health:", await client.health_check())
    try:
        asyncio.run(smoke())
    finally:
        try:
            asyncio.run(client.close())
        except Exception:
            pass
