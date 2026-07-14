"""沙箱编排：Building → Verifying（含一次自愈）。"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from src.configs import get_settings
from src.modules.llm import LocalModelGateway, get_local_model_gateway
from src.modules.models import Task
from src.modules.models.enums import Stage
from src.modules.sandbox.deploy import (
    collect_runtime_logs,
    deploy_mock_process,
    deploy_with_docker,
)
from src.modules.sandbox.docker_cli import docker_available
from src.modules.sandbox.heal import heal_generated_code
from src.modules.sandbox.verify import wait_for_http_ok

logger = logging.getLogger(__name__)

AppendStage = Callable[..., Awaitable[Task]]
FailTask = Callable[..., Awaitable[dict[str, Any]]]


async def build_and_verify(
    task: Task,
    *,
    append_stage: AppendStage,
    fail_task: FailTask,
    gateway: LocalModelGateway | None = None,
    mock: bool | None = None,
) -> dict[str, Any]:
    """在 Coding 完成后执行沙箱构建与验证。"""
    settings = get_settings()
    use_mock = settings.sandbox_mock if mock is None else mock
    if not use_mock and not docker_available():
        logger.warning("docker unavailable; fallback to sandbox mock")
        use_mock = True

    gw = gateway or get_local_model_gateway()
    code_root = task.generated_code_path
    if not code_root:
        return await fail_task(task, message="沙箱构建失败", detail="generated_code_path 为空")

    await append_stage(
        task,
        stage=Stage.Building,
        message="开始沙箱构建",
        detail=f"mock={use_mock} code_root={code_root}",
    )

    healed = False
    last_error = ""

    for attempt in range(2):  # 首次 + 1 次自愈
        deploy = (
            deploy_mock_process(str(task.id), code_root)
            if use_mock
            else deploy_with_docker(str(task.id), code_root)
        )
        if not deploy.ok:
            last_error = deploy.detail
            await append_stage(
                task,
                stage=Stage.Building,
                message=f"构建失败（attempt={attempt + 1}）",
                detail=last_error[:2000],
            )
            if attempt == 0:
                try:
                    code_root = await _heal(
                        task,
                        append_stage=append_stage,
                        code_root=code_root,
                        error_log=last_error,
                        gateway=gw,
                        use_mock=use_mock,
                        phase="编译期",
                    )
                    healed = True
                    continue
                except Exception as exc:
                    return await fail_task(task, message="自愈失败", detail=str(exc))
            return await fail_task(task, message="沙箱构建失败", detail=last_error[:2000])

        task.containers = deploy.containers
        task.exposed_url = deploy.exposed_url
        await append_stage(
            task,
            stage=Stage.Building,
            message="沙箱已拉起",
            detail=f"url={deploy.exposed_url}; {deploy.detail}",
        )

        await append_stage(
            task,
            stage=Stage.Verifying,
            message="开始运行期健康检查",
            detail=f"GET {deploy.exposed_url}/health",
        )
        ok, health_detail = await wait_for_http_ok(f"{deploy.exposed_url}/health")
        if ok:
            # 落库 Success 前再校验运行额度，防止并发创建超限
            from src.modules.models import User
            from src.modules.sandbox.lifecycle import stop_task_runtime
            from src.modules.tasks import repo as task_repo

            settings_quota = get_settings()
            limit = max(1, settings_quota.user_app_running_limit)
            author = task.author
            if not isinstance(author, User):
                try:
                    author = await task.author.fetch()  # type: ignore[union-attr]
                except Exception:
                    author = None
            used = 0
            if isinstance(author, User):
                used = await task_repo.count_running_tasks_for_user(author)
            if used >= limit:
                task.containers = deploy.containers
                task.exposed_url = deploy.exposed_url
                stop_task_runtime(task)
                return await fail_task(
                    task,
                    message="运行额度不足，部署未保留",
                    detail=(
                        f"同时运行上限 {limit}，当前已有 {used} 个运行中应用；"
                        "已停止本次新拉起的容器，请停止其他应用后重试"
                    ),
                )

            await append_stage(
                task,
                stage=Stage.Success,
                message="部署成功",
                detail=f"{health_detail}; healed={healed}",
            )
            return {
                "task_id": str(task.id),
                "current_stage": Stage.Success.value,
                "exposed_url": task.exposed_url,
                "log_count": len(task.logs or []),
                "failed": False,
                "healed": healed,
            }

        runtime_logs = collect_runtime_logs(deploy)
        last_error = f"health check failed: {health_detail}\n{runtime_logs}"
        await append_stage(
            task,
            stage=Stage.Verifying,
            message=f"运行检查失败（attempt={attempt + 1}）",
            detail=last_error[:2000],
        )
        if attempt == 0:
            try:
                code_root = await _heal(
                    task,
                    append_stage=append_stage,
                    code_root=code_root,
                    error_log=last_error,
                    gateway=gw,
                    use_mock=use_mock,
                    phase="运行期",
                )
                healed = True
                continue
            except Exception as exc:
                return await fail_task(task, message="运行期自愈失败", detail=str(exc))
        return await fail_task(task, message="运行验证失败", detail=last_error[:2000])

    return await fail_task(task, message="沙箱流程异常结束", detail=last_error[:2000])


async def _heal(
    task: Task,
    *,
    append_stage: AppendStage,
    code_root: str,
    error_log: str,
    gateway: LocalModelGateway,
    use_mock: bool,
    phase: str,
) -> str:
    settings = get_settings()
    await append_stage(
        task,
        stage=Stage.Building if phase == "编译期" else Stage.Verifying,
        message=f"触发{phase}自愈",
        detail="Seed-Coder / mock heal x1",
    )
    new_root = await heal_generated_code(
        task_id=str(task.id),
        code_root=code_root,
        error_log=error_log,
        gateway=gateway,
        mock=use_mock or settings.ai_mock,
    )
    task.generated_code_path = new_root
    return new_root
