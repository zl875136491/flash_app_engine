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

BACKEND_DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn
COPY backend/ /app/
COPY frontend/ /app/static/
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

FRONTEND_DOCKERFILE = """\
FROM nginx:alpine
COPY frontend/ /usr/share/nginx/html/
RUN printf '%s\\n' \
  'server {' \
  '  listen 8000;' \
  '  server_name _;' \
  '  root /usr/share/nginx/html;' \
  '  location = /health { default_type text/plain; return 200 "ok\\n"; }' \
  '  location / { try_files $uri $uri/ /index.html; }' \
  '}' \
  > /etc/nginx/conf.d/default.conf
EXPOSE 8000
CMD ["nginx", "-g", "daemon off;"]
"""

MINIMAL_BACKEND_MAIN = """\
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="FlashApp Generated")
static_dir = Path(__file__).resolve().parent / "static"
index_file = static_dir / "index.html"


@app.get("/health")
def health():
    return {"status": "ok"}


if static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")


@app.get("/")
def root():
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "ok", "message": "FlashApp generated backend"}
"""

# 兼容旧引用
DEFAULT_DOCKERFILE = BACKEND_DOCKERFILE


@dataclass
class DeployResult:
    ok: bool
    host_port: int
    exposed_url: str
    containers: list[Container]
    detail: str
    container_name: str = ""
    pid: int | None = None


def _backend_main(code_root: Path) -> Path:
    return code_root / "backend" / "main.py"


def _python_syntax_ok(path: Path) -> bool:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        return True
    except Exception:
        return False


def _ensure_frontend_placeholder(code_root: Path) -> None:
    frontend = code_root / "frontend"
    frontend.mkdir(parents=True, exist_ok=True)
    index = frontend / "index.html"
    if not index.exists():
        index.write_text(
            "<!doctype html><html><head><meta charset='utf-8'/>"
            "<title>FlashApp</title></head>"
            "<body><h1>FlashApp</h1><p>generated</p></body></html>\n",
            encoding="utf-8",
        )


def _prepare_code_root(code_root: Path) -> None:
    """按实际产物布局补齐可构建的 Dockerfile / 最小可运行入口。

    常见模型输出只有 frontend，或 backend/main.py 语法损坏；默认 Dockerfile 又假设
    存在 backend/，会导致 COPY 失败或容器启动即崩。这里在构建前做一次本地纠偏。
    """
    _ensure_frontend_placeholder(code_root)
    main_py = _backend_main(code_root)
    backend_ok = main_py.exists() and _python_syntax_ok(main_py)
    dockerfile = code_root / "Dockerfile"

    if not backend_ok:
        if main_py.exists():
            logger.warning("invalid backend/main.py; falling back to frontend nginx image")
        # 无可用后端时，用 nginx 托管静态页，并提供 /health
        dockerfile.write_text(FRONTEND_DOCKERFILE, encoding="utf-8")
        return

    text = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
    needs_rewrite = (
        not text.strip()
        or ("COPY backend" in text and not (code_root / "backend").is_dir())
        or ("COPY backend/" in text and "COPY frontend/" not in text)
    )
    if needs_rewrite or not dockerfile.exists():
        dockerfile.write_text(BACKEND_DOCKERFILE, encoding="utf-8")

    src = main_py.read_text(encoding="utf-8")
    if "/health" not in src:
        logger.warning("backend/main.py missing /health; rewriting minimal app")
        main_py.write_text(MINIMAL_BACKEND_MAIN, encoding="utf-8")


def _ensure_dockerfile(code_root: Path) -> None:
    """兼容旧调用；实际准备逻辑见 _prepare_code_root。"""
    _prepare_code_root(code_root)


def _public_url(port: int) -> str:
    settings = get_settings()
    return f"http://{settings.sandbox_public_host}:{port}"


def deploy_with_docker(task_id: str, code_root: str) -> DeployResult:
    root = Path(code_root)
    _prepare_code_root(root)
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
