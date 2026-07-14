"""DeepSeek-R1-70B：深度推理（/v1/completions + prompt）。"""

from __future__ import annotations

from typing import Any

from src.configs import get_settings
from src.modules.llm.base import HttpModelClient
from src.modules.llm.constants import DEFAULT_TIMEOUT_SECONDS, DEEPSEEK_MODEL_ID
from src.modules.llm.errors import extract_completion_text


class DeepSeekClient(HttpModelClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client=None,
    ):
        settings = get_settings()
        super().__init__(
            base_url=base_url or settings.deepseek_base_url,
            model_id=DEEPSEEK_MODEL_ID,
            timeout=timeout,
            client=client,
        )

    async def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 300,
        temperature: float = 0,
        extra: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if extra:
            payload.update(extra)

        data = await self._post_json("/v1/completions", payload)
        return extract_completion_text(data)
