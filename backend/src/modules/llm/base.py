"""共享 httpx 异步客户端工厂。"""

from __future__ import annotations

from typing import Any

import httpx

from src.modules.llm.constants import DEFAULT_TIMEOUT_SECONDS
from src.modules.llm.errors import raise_for_model_response


class HttpModelClient:
    """OpenAI 兼容 HTTP 客户端基类。"""

    def __init__(
        self,
        *,
        base_url: str,
        model_id: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.timeout = timeout
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        from src.modules.llm.errors import LocalModelError

        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}{path}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        except httpx.RequestError as exc:
            raise LocalModelError(f"模型请求失败: {self.base_url}{path}") from exc
        return await raise_for_model_response(response)

    async def _get_json(self, url: str) -> Any:
        from src.modules.llm.errors import LocalModelError

        client = await self._get_client()
        try:
            response = await client.get(url)
        except httpx.RequestError as exc:
            raise LocalModelError(f"模型请求失败: {url}") from exc
        return await raise_for_model_response(response)
