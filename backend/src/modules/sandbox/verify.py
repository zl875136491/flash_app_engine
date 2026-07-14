"""运行期 HTTP 健康检查。"""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def wait_for_http_ok(
    url: str,
    *,
    attempts: int = 20,
    interval_seconds: float = 0.5,
    timeout_seconds: float = 3.0,
) -> tuple[bool, str]:
    last_error = ""
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        for i in range(attempts):
            try:
                response = await client.get(url)
                if 200 <= response.status_code < 300:
                    return True, f"HTTP {response.status_code}"
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            except Exception as exc:
                last_error = str(exc)
            logger.debug("health attempt=%s url=%s err=%s", i + 1, url, last_error)
            await asyncio.sleep(interval_seconds)
    return False, last_error
