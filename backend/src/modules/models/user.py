"""User 文档模型。"""

from __future__ import annotations

from datetime import datetime

from beanie import Document, Indexed
from pydantic import Field

from src.modules.models.enums import utc_now


class User(Document):
    itcode: Indexed(str, unique=True)  # type: ignore[valid-type]
    name: str = Field(..., description="展示名称")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "users"

    async def touch(self) -> None:
        self.updated_at = utc_now()
        await self.save()
