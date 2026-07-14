"""Beanie 文档模型注册表。"""

from __future__ import annotations

from src.modules.models.image import Image
from src.modules.models.task import Task
from src.modules.models.user import User

DOCUMENT_MODELS: list[type] = [User, Image, Task]

__all__ = ["DOCUMENT_MODELS", "User", "Image", "Task"]
