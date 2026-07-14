"""任务 API 离线冒烟：鉴权、参数校验、DB 不可用时的 503。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.core.app import create_app
from src.modules.auth.jwt import create_access_token


def main() -> None:
    app = create_app()
    client = TestClient(app)

    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    assert "/api/v1/tasks" in paths
    assert "/api/v1/tasks/{task_id}" in paths
    assert "/api/v1/tasks/{task_id}/logs" in paths

    # 未登录
    assert client.get("/api/v1/tasks").status_code == 401
    assert client.post("/api/v1/tasks", json={"raw_voice_text": "hi"}).status_code == 401

    token = create_access_token(itcode="zhangle")
    headers = {"Authorization": f"Bearer {token}"}

    # 空输入
    bad = client.post("/api/v1/tasks", headers=headers, json={})
    assert bad.status_code == 422

    # DB 不可用时应 503（本环境通常无 Mongo）
    create = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"raw_voice_text": "做一个请假审批小应用"},
    )
    assert create.status_code == 503, create.text

    listed = client.get("/api/v1/tasks", headers=headers)
    assert listed.status_code == 503

    print("task api smoke tests passed")


if __name__ == "__main__":
    main()
