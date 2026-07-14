"""Task 文档模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from beanie import Document, Link, before_event, Insert, Replace, Save, Update
from pydantic import Field

from src.modules.models.enums import (
    AllocatedResources,
    Container,
    Stage,
    StageLog,
    utc_now,
)
from src.modules.models.image import Image
from src.modules.models.user import User


class Task(Document):
    author: Link[User] = Field(..., description="任务创建者")

    raw_voice_text: Optional[str] = Field(default=None, description="FunASR 转写后的原始文本")
    images: list[Link[Image]] = Field(default_factory=list, description="辅助图片")
    images_content: list[str] = Field(default_factory=list, description="辅助图片内容列表")

    current_stage: Stage = Field(default=Stage.Received, description="当前阶段")
    logs: list[StageLog] = Field(default_factory=list, description="详细日志流")

    allocated_resources: AllocatedResources = Field(
        default_factory=AllocatedResources,
        description="资源配置",
    )

    generated_code_path: Optional[str] = Field(
        default=None,
        max_length=255,
        description="生成的代码在宿主机的临时根目录",
    )
    containers: list[Container] = Field(default_factory=list, description="容器列表")
    exposed_url: Optional[str] = Field(
        default=None,
        max_length=255,
        description="最终对外的 Web 访问链接",
    )

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "tasks"

    @before_event(Insert, Replace, Save, Update)
    def _set_updated_at(self) -> None:
        self.updated_at = utc_now()

    def append_log(
        self,
        *,
        stage: Stage,
        message: str,
        detail: str = "",
    ) -> None:
        self.current_stage = stage
        self.logs.append(
            StageLog(stage=stage, message=message, detail=detail),
        )
