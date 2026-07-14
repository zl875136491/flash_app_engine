"""Celery 骨架冒烟：eager 模式推进里程碑并写回 Mongo。"""

from __future__ import annotations

import os

# 必须在导入 celery_app / settings 缓存前设置
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:27017")
os.environ.setdefault("MONGODB_DB", "flashapp_celery_smoke")

from src.configs.settings import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from src.core.app import create_app
from src.core.celery_app import celery_app
from src.modules.auth.jwt import create_access_token


def main() -> None:
    settings = get_settings()
    assert settings.celery_task_always_eager is True
    celery_app.conf.task_always_eager = True

    app = create_app()
    with TestClient(app) as client:
        health = client.get("/api/v1/health").json()
        assert health.get("mongodb") == "connected", health

        token = create_access_token(itcode="zhangle")
        headers = {"Authorization": f"Bearer {token}"}
        created = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"raw_voice_text": "Celery 骨架冒烟任务"},
        )
        assert created.status_code == 201, created.text
        task = created.json()
        print("stage", task["current_stage"], "logs", len(task["logs"]))
        assert task["current_stage"] == "Coding", task
        messages = [log["message"] for log in task["logs"]]
        assert any("Worker 已接手" in m for m in messages), messages
        assert any("编码占位" in m or "占位" in m for m in messages), messages

    print("celery skeleton smoke tests passed")


if __name__ == "__main__":
    main()
