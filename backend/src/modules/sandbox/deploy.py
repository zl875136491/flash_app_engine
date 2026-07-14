"""沙箱构建与部署（Docker 或 mock 本地进程）。"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from src.configs import get_settings
from src.modules.models.enums import Container
from src.modules.sandbox.docker_cli import container_logs, docker_available, run_docker
from src.modules.sandbox.ports import allocate_host_port

logger = logging.getLogger(__name__)

DEFAULT_DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn
COPY backend/ /app/
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


@dataclass
class DeployResult:
    ok: bool
    host_port: int
    exposed_url: str
    containers: list[Container]
    detail: str
    container_name: str = ""
    pid: int | None = None


def _ensure_dockerfile(code_root: Path) -> None:
    dockerfile = code_root / "Dockerfile"
    if not dockerfile.exists():
        dockerfile.write_text(DEFAULT_DOCKERFILE, encoding="utf-8")


def _public_url(port: int) -> str:
    settings = get_settings()
    return f"http://{settings.sandbox_public_host}:{port}"


def deploy_with_docker(task_id: str, code_root: str) -> DeployResult:
    root = Path(code_root)
    _ensure_dockerfile(root)
    host_port = allocate_host_port()
    image = f"flashapp-{task_id}".lower()
    name = f"flashapp-{task_id}".lower()

    # 清理同名残留
    run_docker(["rm", "-f", name], timeout=60)
    build = run_docker(["build", "-t", image, str(root)], timeout=600)
    if not build.ok:
        return DeployResult(
            ok=False,
            host_port=host_port,
            exposed_url=_public_url(host_port),
            containers=[],
            detail=f"docker build failed:\n{build.output[-4000:]}",
            container_name=name,
        )

    run = run_docker(
        [
            "run",
            "-d",
            "--name",
            name,
            "-p",
            f"{host_port}:8000",
            image,
        ],
        timeout=120,
    )
    if not run.ok:
        return DeployResult(
            ok=False,
            host_port=host_port,
            exposed_url=_public_url(host_port),
            containers=[],
            detail=f"docker run failed:\n{run.output[-4000:]}",
            container_name=name,
        )

    containers = [
        Container(
            name=name,
            image=image,
            ports=[host_port],
            environment={},
            volumes=[],
            command=[],
        )
    ]
    return DeployResult(
        ok=True,
        host_port=host_port,
        exposed_url=_public_url(host_port),
        containers=containers,
        detail="docker deployed",
        container_name=name,
    )


def deploy_mock_process(task_id: str, code_root: str) -> DeployResult:
    """无 Docker 时：用静态文件服务模拟暴露入口，供验证与冒烟。"""
    root = Path(code_root)
    frontend = root / "frontend"
    frontend.mkdir(parents=True, exist_ok=True)
    index = frontend / "index.html"
    if not index.exists():
        index.write_text(
            "<!doctype html><html><body><h1>FlashApp Sandbox</h1></body></html>\n",
            encoding="utf-8",
        )
    # 便于健康检查：/health 映射为静态文件
    (frontend / "health").write_text("ok\n", encoding="utf-8")

    host_port = allocate_host_port()
    # 后台 python http.server
    proc = subprocess.Popen(
        ["python3", "-m", "http.server", str(host_port), "--bind", "127.0.0.1"],
        cwd=str(frontend),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # 短暂等待监听
    time.sleep(0.3)
    if proc.poll() is not None:
        return DeployResult(
            ok=False,
            host_port=host_port,
            exposed_url=_public_url(host_port),
            containers=[],
            detail="mock http.server 启动失败",
            pid=proc.pid,
        )

    # 记录 pid 便于后续清理
    pid_file = root / ".sandbox.pid"
    pid_file.write_text(str(proc.pid), encoding="utf-8")

    name = f"mock-{task_id}"
    containers = [
        Container(
            name=name,
            image="python3-http.server",
            ports=[host_port],
            environment={"MODE": "mock"},
            volumes=[str(frontend)],
            command=["python3", "-m", "http.server", str(host_port)],
        )
    ]
    return DeployResult(
        ok=True,
        host_port=host_port,
        exposed_url=_public_url(host_port),
        containers=containers,
        detail=f"mock server pid={proc.pid}",
        container_name=name,
        pid=proc.pid,
    )


def stop_mock_process(code_root: str) -> None:
    pid_file = Path(code_root) / ".sandbox.pid"
    if not pid_file.exists():
        return
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        os.killpg(pid, signal.SIGTERM)
    except Exception:
        logger.debug("stop mock process failed", exc_info=True)


def collect_runtime_logs(deploy: DeployResult) -> str:
    if deploy.container_name and docker_available() and not deploy.container_name.startswith("mock-"):
        return container_logs(deploy.container_name, tail=50)
    return deploy.detail
