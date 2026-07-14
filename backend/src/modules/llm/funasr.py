"""FunASR：实时语音识别（WebSocket，PCM16 / 16kHz / mono）。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable, Sequence
from typing import Any

import websockets
from websockets.asyncio.client import connect as ws_connect

from src.configs import get_settings
from src.modules.llm.constants import FUNASR_TIMEOUT_SECONDS
from src.modules.llm.errors import LocalModelError


class FunASRClient:
    def __init__(
        self,
        *,
        ws_url: str | None = None,
        open_timeout: float = FUNASR_TIMEOUT_SECONDS,
    ):
        settings = get_settings()
        self.ws_url = ws_url or settings.funasr_ws_url
        self.open_timeout = open_timeout

    async def recognize(
        self,
        pcm_chunks: Sequence[bytes] | Iterable[bytes],
        *,
        collect_partial: bool = True,
    ) -> str:
        """发送 PCM 分片，返回最终拼接文本。"""
        texts: list[str] = []
        async for item in self.stream_recognize(pcm_chunks):
            text = item.get("text")
            if text:
                texts.append(text)
                if not collect_partial:
                    # 仍收集全部；该参数预留给调用方过滤策略
                    pass
        return "".join(texts).strip()

    async def stream_recognize(
        self,
        pcm_chunks: Sequence[bytes] | Iterable[bytes],
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            async with ws_connect(self.ws_url, open_timeout=self.open_timeout) as ws:
                for chunk in pcm_chunks:
                    if not chunk:
                        continue
                    await ws.send(chunk)
                await ws.send(json.dumps({"type": "end"}))
                async for raw in ws:
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        yield {"text": str(raw)}
                        continue
                    if isinstance(data, dict):
                        yield data
                    else:
                        yield {"text": str(data)}
        except Exception as exc:
            raise LocalModelError(f"FunASR 连接失败: {self.ws_url}") from exc
