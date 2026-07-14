"""Worker 侧 Mongo / Beanie 初始化（Celery Worker 进程使用）。"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from src.core.database import close_db, connect_db, is_db_ready

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def ensure_worker_db() -> None:
    if not is_db_ready():
        await connect_db()
        if not is_db_ready():
            raise RuntimeError("Worker 无法连接 MongoDB")


def run_async(coro_factory: Callable[[], Awaitable[T]]) -> T:
    """在独立 Celery Worker 进程中执行异步协程（进程内无运行中的事件循环）。"""
    return asyncio.run(_run_with_db(coro_factory))


async def _run_with_db(coro_factory: Callable[[], Awaitable[T]]) -> T:
    await ensure_worker_db()
    try:
        return await coro_factory()
    finally:
        await close_db()
