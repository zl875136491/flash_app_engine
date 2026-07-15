"""Celery 应用实例。"""

from __future__ import annotations

from celery import Celery

from src.configs import get_settings

settings = get_settings()

celery_app = Celery(
    "flashapp",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.modules.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # 开发/冒烟可设 CELERY_TASK_ALWAYS_EAGER=true，同步执行不依赖 Redis
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    task_default_queue="flashapp",
)
