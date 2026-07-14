"""Qwen3.6-35B-A3B：多模态对话 + OCR。"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from src.configs import get_settings
from src.modules.llm.base import HttpModelClient
from src.modules.llm.constants import DEFAULT_TIMEOUT_SECONDS, QWEN_MODEL_ID
from src.modules.llm.errors import extract_chat_content


class QwenClient(HttpModelClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client=None,
    ):
        settings = get_settings()
        super().__init__(
            base_url=base_url or settings.qwen_base_url,
            model_id=QWEN_MODEL_ID,
            timeout=timeout,
            client=client,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_thinking: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
            "extra_body": {
                "chat_template_kwargs": {"enable_thinking": enable_thinking},
            },
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)

        data = await self._post_json("/v1/chat/completions", payload)
        return extract_chat_content(data)

    async def ocr(
        self,
        *,
        image_bytes: bytes | None = None,
        image_path: str | Path | None = None,
        mime_type: str = "image/jpeg",
        prompt: str = "请识别这张图片中的所有文字",
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        if image_bytes is None:
            if image_path is None:
                raise ValueError("必须提供 image_bytes 或 image_path")
            image_bytes = Path(image_path).read_bytes()

        b64 = base64.b64encode(image_bytes).decode("ascii")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                    },
                ],
            }
        ]
        return await self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=False,
        )
