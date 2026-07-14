"""Seed-Coder：代码生成。"""

from __future__ import annotations

from typing import Any

from src.configs import get_settings
from src.modules.llm.base import HttpModelClient
from src.modules.llm.constants import DEFAULT_TIMEOUT_SECONDS, SEEDCODER_MODEL_ID
from src.modules.llm.errors import extract_chat_content


class SeedCoderClient(HttpModelClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client=None,
    ):
        settings = get_settings()
        super().__init__(
            base_url=base_url or settings.seedcoder_base_url,
            model_id=SEEDCODER_MODEL_ID,
            timeout=timeout,
            client=client,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        enable_thinking: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        # 原始 HTTP 请求需把 chat_template_kwargs 放在 body 顶层（勿嵌套 extra_body）。
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)

        data = await self._post_json("/v1/chat/completions", payload)
        return extract_chat_content(data)

    async def generate_code(self, prompt: str, *, system: str | None = None) -> str:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(messages)
