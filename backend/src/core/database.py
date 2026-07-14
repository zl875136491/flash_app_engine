import logging

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from src.configs import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db_ready: bool = False


def _default_document_models() -> list:
    from src.modules.models import DOCUMENT_MODELS

    return list(DOCUMENT_MODELS)


async def connect_db(document_models: list | None = None) -> None:
    """初始化 MongoDB 连接与 Beanie ODM。

    默认注册 `src.modules.models.DOCUMENT_MODELS`；也可显式传入覆盖。
    开发环境下连接失败仅记录警告，不阻断进程启动（便于先跑通健康检查）。
    """
    global _client, _db_ready
    settings = get_settings()
    models = document_models if document_models is not None else _default_document_models()
    try:
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=3000,
        )
        # 主动探测，避免懒连接延迟报错
        await _client.admin.command("ping")
        await init_beanie(
            database=_client[settings.mongodb_db],
            document_models=models,
        )
        _db_ready = True
        logger.info(
            "MongoDB connected: %s / %s (models=%s)",
            settings.mongodb_uri,
            settings.mongodb_db,
            [m.__name__ for m in models],
        )
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
