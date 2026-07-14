"""Celery 任务定义。"""

from __future__ import annotations

import logging

from src.core.celery_app import celery_app
from src.modules.worker.db import run_async
from src.modules.worker.pipeline import run_pipeline_skeleton

logger = logging.getLogger(__name__)


@celery_app.task(name="flashapp.process_task", bind=True, max_retries=3)
def process_flashapp_task(self, task_id: str) -> dict:
    """消费单个 FlashApp 任务，推进里程碑并写回数据库。"""
    logger.info("celery received task_id=%s retries=%s", task_id, self.request.retries)
    try:
        result = run_async(lambda: run_pipeline_skeleton(task_id))
        logger.info("celery finished task_id=%s result=%s", task_id, result)
        return result
    except ValueError:
        # 任务不存在等业务错误不重试
        logger.exception("celery business error task_id=%s", task_id)
        raise
    except Exception as exc:
        logger.exception("celery failed task_id=%s", task_id)
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 30)) from exc
