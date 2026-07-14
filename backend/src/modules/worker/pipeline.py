"""编排流水线骨架：推进里程碑并写回 Mongo（AI / 沙箱在后续任务点接入）。"""

from __future__ import annotations

import logging

from src.modules.models import Task
from src.modules.models.enums import Stage, utc_now
from src.modules.tasks.repo import get_task_by_id

logger = logging.getLogger(__name__)


async def append_stage(
    task: Task,
    *,
    stage: Stage,
    message: str,
    detail: str = "",
) -> Task:
    task.append_log(stage=stage, message=message, detail=detail)
    task.updated_at = utc_now()
    await task.save()
    return task


async def run_pipeline_skeleton(task_id: str) -> dict:
    """骨架流水线：Received -> Analyzing（占位）-> Coding（占位）后暂停。

    真实 Analyzing/Coding 由任务点 7 实现；Building/Verifying 由任务点 8 实现。
    """
    task = await get_task_by_id(task_id)
    if task is None:
        raise ValueError(f"任务不存在: {task_id}")

    logger.info("pipeline start task_id=%s stage=%s", task_id, task.current_stage)

    await append_stage(
        task,
        stage=Stage.Analyzing,
        message="Worker 已接手任务",
        detail="Celery 骨架：开始架构解析占位",
    )

    await append_stage(
        task,
        stage=Stage.Coding,
        message="进入全栈编码占位阶段",
        detail="等待任务点 7（AI 编排）接入真实代码生成",
    )

    # 重新读取，返回摘要
    task = await get_task_by_id(task_id)
    assert task is not None
    return {
        "task_id": task_id,
        "current_stage": task.current_stage.value,
        "log_count": len(task.logs or []),
    }
