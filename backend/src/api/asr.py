"""FunASR WebSocket 同源代理：浏览器连 wss://本服务，后端再连内网 ws://FunASR。"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed

from src.configs import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["asr"])


@router.websocket("/asr/ws")
async def funasr_proxy(client_ws: WebSocket) -> None:
    """将浏览器 PCM/JSON 双向转发到 FunASR。

    前端应连接：`wss://<host>/api/v1/asr/ws`（与页面同源，避免混合内容）。
    """
    await client_ws.accept()
    settings = get_settings()
    upstream_url = settings.funasr_ws_url
    logger.info("FunASR proxy connecting to %s", upstream_url)

    try:
        async with ws_connect(upstream_url, open_timeout=8) as upstream:

            async def client_to_upstream() -> None:
                try:
                    while True:
                        message = await client_ws.receive()
                        if message.get("type") == "websocket.disconnect":
                            break
                        if message.get("bytes") is not None:
                            await upstream.send(message["bytes"])
                        elif message.get("text") is not None:
                            await upstream.send(message["text"])
                except WebSocketDisconnect:
                    pass

            async def upstream_to_client() -> None:
                try:
                    async for message in upstream:
                        if isinstance(message, bytes):
                            await client_ws.send_bytes(message)
                        else:
                            await client_ws.send_text(str(message))
                except ConnectionClosed:
                    pass

            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(client_to_upstream()),
                    asyncio.create_task(upstream_to_client()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                exc = task.exception()
                if exc:
                    logger.warning("FunASR proxy task error: %s", exc)
    except Exception as exc:
        logger.exception("FunASR proxy failed: %s", exc)
        try:
            await client_ws.send_text(
                '{"text":"","error":"FunASR 上游不可达，请检查内网或改用手动输入"}'
            )
        except Exception:
            pass
    finally:
        try:
            await client_ws.close()
        except Exception:
            pass
