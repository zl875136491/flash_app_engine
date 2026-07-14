"""Image 文档模型（辅助上传图）。"""

from __future__ import annotations

from datetime import datetime

from beanie import Document, Link
from pydantic import Field

from src.modules.models.enums import utc_now
from src.modules.models.user import User


class Image(Document):
    """PRD 原稿为 BaseModel，但 Task.images 使用 Link，故落地为独立 Document。"""

    path: str = Field(..., description="图片路径")
    author: Link[User] = Field(..., description="上传人")
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "images"
