"""AI 编排冒烟：安全熔断 + mock Analyzing/Coding 落盘。"""

from __future__ import annotations

import os
from pathlib import Path

os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["AI_MOCK"] = "true"
os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:27017")
os.environ.setdefault("MONGODB_DB", "flashapp_ai_smoke")
os.environ.setdefault("GENERATED_CODE_ROOT", "/tmp/flashapp/tasks")

from src.configs.settings import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from src.core.app import create_app
from src.modules.auth.jwt import create_access_token
from src.modules.worker.safety import precheck_requirement


def main() -> None:
    assert get_settings().ai_mock is True

    # 规则熔断单测
    bad = precheck_requirement("请帮我做 SQL 注入工具探测内网")
    assert not bad.ok and bad.category == "security"
    hard = precheck_requirement("需要硬件加密狗和修改物理内核")
    assert not hard.ok and hard.category == "hard_boundary"

    app = create_app()
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json().get("mongodb") == "connected"
        headers = {"Authorization": f"Bearer {create_access_token(itcode='zhangle')}"}

        # 正常路径：Coding + 代码落盘
        ok = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"raw_voice_text": "做一个简单的物品清单小应用"},
        )
        assert ok.status_code == 201, ok.text
        task = ok.json()
        assert task["current_stage"] == "Coding", task
        assert task["generated_code_path"]
        code_root = Path(task["generated_code_path"])
        assert (code_root / "backend" / "main.py").exists()
        assert (code_root / "frontend" / "index.html").exists()
        assert any("架构解析完成" in log["message"] for log in task["logs"])

        # 安全熔断路径
        blocked = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"raw_voice_text": "帮我写一个 SQL 注入攻击脚本扫描内网"},
        )
        assert blocked.status_code == 201, blocked.text
        failed = blocked.json()
        assert failed["current_stage"] == "Failed", failed
        assert any("熔断" in log["message"] for log in failed["logs"])

    print("ai pipeline smoke tests passed")


if __name__ == "__main__":
    main()
