"""沙箱运行时生命周期：停止 / 启动 / 移除。"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.configs import get_settings
from src.modules.models import Task
from src.modules.models.enums import Container
from src.modules.sandbox.docker_cli import docker_available, run_docker
from src.modules.sandbox.deploy import _public_url, stop_mock_process
from src.modules.sandbox.ports import allocate_host_port

logger = logging.getLogger(__name__)


@dataclass
class LifecycleResult:
    ok: bool
    detail: str
    exposed_url: str | None = None
    containers: list[Container] | None = None


def _container_names(task: Task) -> list[str]:
    names: list[str] = []
    for item in task.containers or []:
        name = (item.name or "").strip()
        if name and name not in names:
            names.append(name)
    if not names:
        # 约定命名兜底
        names.append(f"flashapp-{task.id}".lower())
    return names


def _is_mock_task(task: Task) -> bool:
    for item in task.containers or []:
        if (item.image or "").startswith("python3-http.server") or (item.name or "").startswith(
            "mock-"
        ):
            return True
        if (item.environment or {}).get("MODE") == "mock":
            return True
    return False


def stop_task_runtime(task: Task) -> LifecycleResult:
    """停止运行中的容器/进程，保留镜像与元数据。"""
    if _is_mock_task(task) or (task.generated_code_path and not docker_available()):
        if task.generated_code_path:
            stop_mock_process(task.generated_code_path)
        return LifecycleResult(ok=True, detail="mock process stopped")

    if not docker_available():
        return LifecycleResult(ok=False, detail="Docker 不可用，无法停止容器")

    details: list[str] = []
    ok = True
    for name in _container_names(task):
        result = run_docker(["stop", name], timeout=60)
        details.append(f"stop {name}: rc={result.returncode}")
        if not result.ok and "No such container" not in (result.stderr or ""):
            ok = False
            details.append(result.output[-500:])
    return LifecycleResult(ok=ok, detail="; ".join(details) or "stopped")


def start_task_runtime(task: Task) -> LifecycleResult:
    """启动已停止的应用：优先 docker start，否则按镜像重建。"""
    if _is_mock_task(task):
        from src.modules.sandbox.deploy import deploy_mock_process

        if not task.generated_code_path:
            return LifecycleResult(ok=False, detail="缺少 generated_code_path，无法启动 mock")
        deploy = deploy_mock_process(str(task.id), task.generated_code_path)
        return LifecycleResult(
            ok=deploy.ok,
            detail=deploy.detail,
            exposed_url=deploy.exposed_url if deploy.ok else None,
            containers=deploy.containers if deploy.ok else None,
        )

    if not docker_available():
        return LifecycleResult(ok=False, detail="Docker 不可用，无法启动容器")

    names = _container_names(task)
    primary = names[0]
    inspect = run_docker(["inspect", "-f", "{{.State.Status}}", primary], timeout=30)
    if inspect.ok:
        start = run_docker(["start", primary], timeout=60)
        if start.ok:
            # 尽量复用已记录的 URL / 端口
            url = task.exposed_url
            if not url and task.containers and task.containers[0].ports:
                url = _public_url(task.containers[0].ports[0])
            return LifecycleResult(
                ok=True,
                detail=f"docker start {primary}",
                exposed_url=url,
                containers=list(task.containers or []),
            )
        # start 失败则尝试重建

    # 容器不存在：用已有镜像重新 run
    image = ""
    if task.containers:
        image = (task.containers[0].image or "").strip()
    if not image:
        image = f"flashapp-{task.id}".lower()

    image_ok = run_docker(["image", "inspect", image], timeout=30)
    if not image_ok.ok:
        return LifecycleResult(
            ok=False,
            detail=f"镜像不存在且容器已丢失，请重新部署或移除任务: {image}",
        )

    host_port = allocate_host_port()
    name = f"flashapp-{task.id}".lower()
    run_docker(["rm", "-f", name], timeout=60)
    run = run_docker(
        ["run", "-d", "--name", name, "-p", f"{host_port}:8000", image],
        timeout=120,
    )
    if not run.ok:
        return LifecycleResult(ok=False, detail=f"docker run failed:\n{run.output[-2000:]}")

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
    return LifecycleResult(
        ok=True,
        detail=f"docker run {name} on {host_port}",
        exposed_url=_public_url(host_port),
        containers=containers,
    )


def remove_task_runtime(task: Task) -> LifecycleResult:
    """删除容器/进程、可选镜像，并清理生成代码目录。"""
    details: list[str] = []

    if _is_mock_task(task) and task.generated_code_path:
        stop_mock_process(task.generated_code_path)
        details.append("mock stopped")
    elif docker_available():
        for name in _container_names(task):
            rm = run_docker(["rm", "-f", name], timeout=60)
            details.append(f"rm {name}: rc={rm.returncode}")
        for item in task.containers or []:
            image = (item.image or "").strip()
            if image and image.startswith("flashapp-"):
                rmi = run_docker(["rmi", "-f", image], timeout=120)
                details.append(f"rmi {image}: rc={rmi.returncode}")

    if task.generated_code_path:
        root = Path(task.generated_code_path)
        settings = get_settings()
        allowed = Path(settings.generated_code_root).resolve()
        try:
            resolved = root.resolve()
            if str(resolved).startswith(str(allowed)) and resolved.exists():
                shutil.rmtree(resolved, ignore_errors=True)
                details.append(f"removed code {resolved}")
        except Exception as exc:
            details.append(f"code cleanup error: {exc}")

    return LifecycleResult(ok=True, detail="; ".join(details) or "removed")
