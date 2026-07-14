"""任务入队封装。"""

from __future__ import annotations

import logging

from src.configs import get_settings
from src.core.celery_app import celery_app
from src.modules.worker.tasks import process_flashapp_task

logger = logging.getLogger(__name__)


def enqueue_process_task(task_id: str) -> str | None:
    """将任务投递到 Celery broker。

    返回 Celery async result id；broker 不可用时返回 None。
    注意：eager 模式请走 `run_pipeline_skeleton` 异步直调，避免与 FastAPI 事件循环冲突。
    """
    if get_settings().celery_task_always_eager:
        logger.debug("skip broker enqueue in eager mode task_id=%s", task_id)
        return "eager-inline"

    celery_app.conf.task_always_eager = False
    try:
        async_result = process_flashapp_task.delay(task_id)
        logger.info("enqueued task_id=%s celery_id=%s", task_id, async_result.id)
        return str(async_result.id) if async_result.id is not None else "unknown"
    except Exception:
        logger.exception("enqueue failed task_id=%s", task_id)
        return None
