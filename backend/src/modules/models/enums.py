"""领域枚举与嵌入式结构（非独立集合）。"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Stage(str, Enum):
    Received = "Received"
    Analyzing = "Analyzing"
    Coding = "Coding"
    Building = "Building"
    Verifying = "Verifying"
    Success = "Success"
    Failed = "Failed"


class AllocatedResources(BaseModel):
    frontend: Optional[bool] = True
    backend: Optional[bool] = True
    db: Optional[bool] = True


class StageLog(BaseModel):
    stage: Stage = Field(..., description="阶段")
    message: str = Field(..., description="日志消息")
    detail: str = Field(default="", description="详细日志")
    created_at: datetime = Field(default_factory=utc_now, description="创建时间")


class Container(BaseModel):
    """任务内嵌的容器规格。

    PRD 原稿将 Container 标为 Document，但 Task.containers 为列表嵌套；
    实际以嵌入文档建模，避免多余集合与 Link 往返。
    """

    name: str = Field(..., description="容器名称")
    image: str = Field(..., description="容器镜像")
    ports: list[int] = Field(default_factory=list, description="容器端口")
    environment: dict[str, str] = Field(default_factory=dict, description="容器环境变量")
    volumes: list[str] = Field(default_factory=list, description="容器挂载卷")
    command: list[str] = Field(default_factory=list, description="容器启动命令")
