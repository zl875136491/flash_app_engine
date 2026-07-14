"""核心数据模型（Beanie ODM）。

对外导出文档类、枚举与注册表，供 database 初始化与业务模块使用。
"""

from src.modules.models.enums import (
    AllocatedResources,
    Container,
    Stage,
    StageLog,
    utc_now,
)
from src.modules.models.image import Image
from src.modules.models.registry import DOCUMENT_MODELS
from src.modules.models.task import Task
from src.modules.models.user import User
from src.modules.models.user_repo import get_or_create_user, get_user_by_itcode

__all__ = [
    "AllocatedResources",
    "Container",
    "DOCUMENT_MODELS",
    "Image",
    "Stage",
    "StageLog",
    "Task",
    "User",
    "get_or_create_user",
    "get_user_by_itcode",
    "utc_now",
]
