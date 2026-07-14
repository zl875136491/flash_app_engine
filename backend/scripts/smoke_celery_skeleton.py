"""Celery / 流水线冒烟（兼容任务点 6）：eager + AI_MOCK。"""

from __future__ import annotations

import os

os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["AI_MOCK"] = "true"
os.environ["SANDBOX_MOCK"] = "true"
os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:27017")
os.environ.setdefault("MONGODB_DB", "flashapp_celery_smoke")
os.environ.setdefault("GENERATED_CODE_ROOT", "/tmp/flashapp/tasks")

from src.configs.settings import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from src.core.app import create_app
from src.core.celery_app import celery_app
from src.modules.auth.jwt import create_access_token


def main() -> None:
    settings = get_settings()
    assert settings.celery_task_always_eager is True
    assert settings.ai_mock is True
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
        assert task["current_stage"] == "Success", task
        messages = [log["message"] for log in task["logs"]]
        assert any("架构解析完成" in m or "代码已生成" in m for m in messages), messages
        assert task.get("generated_code_path")
        assert task.get("exposed_url")

    print("celery skeleton smoke tests passed")


if __name__ == "__main__":
    main()
