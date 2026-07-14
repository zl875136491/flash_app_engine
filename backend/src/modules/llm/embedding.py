"""Qwen3-VL-Embedding：向量嵌入。"""

from __future__ import annotations

from typing import Any

from src.configs import get_settings
from src.modules.llm.base import HttpModelClient
from src.modules.llm.constants import DEFAULT_TIMEOUT_SECONDS, EMBEDDING_MODEL_ID
from src.modules.llm.errors import LocalModelError


class EmbeddingClient(HttpModelClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client=None,
    ):
        settings = get_settings()
        super().__init__(
            base_url=base_url or settings.embedding_base_url,
            model_id=EMBEDDING_MODEL_ID,
            timeout=timeout,
            client=client,
        )

    async def embed(self, input_text: str | list[str]) -> list[list[float]]:
        payload: dict[str, Any] = {
            "model": self.model_id,
            "input": input_text,
        }
        data = await self._post_json("/v1/embeddings", payload)
        try:
            items = data["data"]
            # OpenAI 风格：按 index 排序
            ordered = sorted(items, key=lambda x: x.get("index", 0))
            return [item["embedding"] for item in ordered]
        except (KeyError, TypeError) as exc:
            raise LocalModelError("响应缺少 data[].embedding", body=data) from exc
