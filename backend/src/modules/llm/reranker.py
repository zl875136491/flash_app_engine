"""Qwen3-VL-Reranker：文档重排。"""

from __future__ import annotations

from typing import Any

from src.configs import get_settings
from src.modules.llm.base import HttpModelClient
from src.modules.llm.constants import DEFAULT_TIMEOUT_SECONDS, RERANKER_MODEL_ID


class RerankerClient(HttpModelClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client=None,
    ):
        settings = get_settings()
        super().__init__(
            base_url=base_url or settings.reranker_base_url,
            model_id=RERANKER_MODEL_ID,
            timeout=timeout,
            client=client,
        )

    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model_id,
            "query": query,
            "documents": documents,
        }
        return await self._post_json("/v1/rerank", payload)
