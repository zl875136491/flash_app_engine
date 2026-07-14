"""沙箱冒烟：mock 部署 + 健康检查 → Success。"""

from __future__ import annotations

import os

os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["AI_MOCK"] = "true"
os.environ["SANDBOX_MOCK"] = "true"
os.environ["SANDBOX_PUBLIC_HOST"] = "127.0.0.1"
os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:27017")
os.environ.setdefault("MONGODB_DB", "flashapp_sandbox_smoke")
os.environ.setdefault("GENERATED_CODE_ROOT", "/tmp/flashapp/tasks")

from src.configs.settings import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from src.core.app import create_app
from src.modules.auth.jwt import create_access_token
from src.modules.sandbox.ports import allocate_host_port


def main() -> None:
    assert get_settings().sandbox_mock is True
    port = allocate_host_port(port_min=30000, port_max=30010)
    assert 30000 <= port <= 30010

    app = create_app()
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json().get("mongodb") == "connected"
        headers = {"Authorization": f"Bearer {create_access_token(itcode='zhangle')}"}
        created = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"raw_voice_text": "做一个简单的展示页"},
        )
        assert created.status_code == 201, created.text
        task = created.json()
        print("stage", task["current_stage"], "url", task.get("exposed_url"))
        assert task["current_stage"] == "Success", task
        assert task["exposed_url"]
        assert task["containers"]
        assert any(log["stage"] == "Building" for log in task["logs"])
        assert any(log["stage"] == "Verifying" for log in task["logs"])
        assert any(log["stage"] == "Success" for log in task["logs"])

        # 外部可访问健康检查
        import httpx

        health = httpx.get(f"{task['exposed_url']}/health", timeout=3.0)
        assert health.status_code == 200, health.text

    print("sandbox smoke tests passed")


if __name__ == "__main__":
    main()
