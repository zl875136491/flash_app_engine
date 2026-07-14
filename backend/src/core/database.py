import logging

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from src.configs import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db_ready: bool = False


async def connect_db(document_models: list | None = None) -> None:
    """初始化 MongoDB 连接与 Beanie ODM。

    document_models 在任务点 3 引入业务模型后再传入；脚手架阶段允许为空列表。
    开发环境下连接失败仅记录警告，不阻断进程启动（便于先跑通健康检查）。
    """
    global _client, _db_ready
    settings = get_settings()
    try:
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=3000,
        )
        # 主动探测，避免懒连接延迟报错
        await _client.admin.command("ping")
        await init_beanie(
            database=_client[settings.mongodb_db],
            document_models=document_models or [],
        )
        _db_ready = True
        logger.info("MongoDB connected: %s / %s", settings.mongodb_uri, settings.mongodb_db)
    except Exception as exc:
        _db_ready = False
        if settings.is_development:
            logger.warning("MongoDB unavailable (%s); continuing in degraded mode", exc)
            if _client is not None:
                _client.close()
                _client = None
        else:
            raise


async def close_db() -> None:
    global _client, _db_ready
    if _client is not None:
        _client.close()
        _client = None
    _db_ready = False


def is_db_ready() -> bool:
    return _db_ready


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("MongoDB 尚未初始化，请先调用 connect_db()")
    return _client
