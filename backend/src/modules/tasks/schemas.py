"""任务 API 的请求 / 响应 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.modules.models.enums import AllocatedResources, Container, Stage


class CreateTaskRequest(BaseModel):
    raw_voice_text: Optional[str] = Field(
        default=None,
        description="FunASR 转写文本或用户直接输入的需求描述",
    )
    images_content: list[str] = Field(
        default_factory=list,
        description="图片 OCR / 描述文本（可先由前端或后续流水线填充）",
    )
    image_paths: list[str] = Field(
        default_factory=list,
        description="已上传图片在宿主机/对象存储上的路径",
    )

    @field_validator("raw_voice_text")
    @classmethod
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @model_validator(mode="after")
    def require_input(self) -> "CreateTaskRequest":
        has_text = bool(self.raw_voice_text)
        has_images = bool(self.image_paths) or bool(self.images_content)
        if not has_text and not has_images:
            raise ValueError("至少提供 raw_voice_text、image_paths 或 images_content 之一")
        return self


class StageLogOut(BaseModel):
    stage: Stage
    message: str
    detail: str = ""
    created_at: datetime


class TaskSummary(BaseModel):
    id: str
    author_itcode: str
    raw_voice_text: Optional[str] = None
    current_stage: Stage
    exposed_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaskDetail(TaskSummary):
    images_content: list[str] = Field(default_factory=list)
    image_paths: list[str] = Field(default_factory=list)
    logs: list[StageLogOut] = Field(default_factory=list)
    allocated_resources: AllocatedResources
    generated_code_path: Optional[str] = None
    containers: list[Container] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    items: list[TaskSummary]
    total: int
