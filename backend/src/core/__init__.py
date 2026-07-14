"""核心包：应用工厂与数据库。

避免在包初始化时导入 app（会间接拉取 api 路由，形成循环依赖）。
请直接使用：
  from src.core.app import create_app
  from src.core.database import connect_db, is_db_ready
"""

__all__ = ["create_app", "connect_db", "close_db", "get_client", "is_db_ready"]


def __getattr__(name: str):
    if name == "create_app":
        from src.core.app import create_app

        return create_app
    if name in {"connect_db", "close_db", "get_client", "is_db_ready"}:
        from src.core import database as db

        return getattr(db, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
