"""编排流水线：安全审查 → Analyzing → Coding → Building → Verifying。"""

from __future__ import annotations

import logging

from src.configs import get_settings
from src.modules.llm import LocalModelGateway, get_local_model_gateway
from src.modules.models import Task
from src.modules.models.enums import Stage, utc_now
from src.modules.sandbox import build_and_verify
from src.modules.tasks.repo import get_task_by_id
from src.modules.worker.analyzing import analyze_requirement, resources_from_plan
from src.modules.worker.coding import generate_code, write_code_bundle
from src.modules.worker.safety import build_requirement_text, precheck_requirement

logger = logging.getLogger(__name__)


async def append_stage(
    task: Task,
    *,
    stage: Stage,
    message: str,
    detail: str = "",
) -> Task:
    task.append_log(stage=stage, message=message, detail=detail)
    task.updated_at = utc_now()
    await task.save()
    return task


async def fail_task(task: Task, *, message: str, detail: str) -> dict:
    await append_stage(task, stage=Stage.Failed, message=message, detail=detail)
    return {
        "task_id": str(task.id),
        "current_stage": Stage.Failed.value,
        "log_count": len(task.logs or []),
        "failed": True,
    }


async def run_pipeline(
    task_id: str,
    *,
    gateway: LocalModelGateway | None = None,
    mock: bool | None = None,
) -> dict:
    """完整编排至部署验证（Building/Verifying 可 mock）。"""
    task = await get_task_by_id(task_id)
    if task is None:
        raise ValueError(f"任务不存在: {task_id}")

    settings = get_settings()
    use_mock = settings.ai_mock if mock is None else mock
    gw = gateway or get_local_model_gateway()

    requirement = build_requirement_text(
        raw_voice_text=task.raw_voice_text,
        images_content=list(task.images_content or []),
    )
    logger.info("pipeline start task_id=%s mock=%s", task_id, use_mock)

    await append_stage(
        task,
        stage=Stage.Analyzing,
        message="开始安全审查与架构解析",
        detail=f"requirement_chars={len(requirement)} mock={use_mock}",
    )

    safety = precheck_requirement(requirement)
    if not safety.ok:
        return await fail_task(
            task,
            message="安全/硬边界熔断",
            detail=f"[{safety.category}] {safety.reason}",
        )

    try:
        plan = await analyze_requirement(requirement, gateway=gw, mock=use_mock)
    except Exception as exc:
        logger.exception("analyze failed task_id=%s", task_id)
        return await fail_task(
            task,
            message="架构解析失败",
            detail=str(exc),
        )

    if plan.get("security_violation") or plan.get("hard_boundary_violation") or plan.get("safe") is False:
        reason = (
            plan.get("security_reason")
            or plan.get("violation_reason")
            or "模型判定需求不可继续"
        )
        return await fail_task(
            task,
            message="架构解析触发熔断",
            detail=str(reason),
        )

    task.allocated_resources = resources_from_plan(plan)
    await append_stage(
        task,
        stage=Stage.Analyzing,
        message="架构解析完成",
        detail=str(plan.get("summary") or plan)[:2000],
    )

    await append_stage(
        task,
        stage=Stage.Coding,
        message="开始全栈代码生成",
        detail="调用 Seed-Coder / mock 生成器",
    )

    try:
        bundle = await generate_code(
            requirement=requirement,
            plan=plan,
            gateway=gw,
            mock=use_mock,
        )
        code_root = write_code_bundle(task_id, bundle)
    except Exception as exc:
        logger.exception("coding failed task_id=%s", task_id)
        return await fail_task(
            task,
            message="代码生成失败",
            detail=str(exc),
        )

    task.generated_code_path = code_root
    await append_stage(
        task,
        stage=Stage.Coding,
        message="代码已生成",
        detail=f"path={code_root}; files={len(bundle.get('files') or [])}; notes={bundle.get('notes', '')}",
    )

    return await build_and_verify(
        task,
        append_stage=append_stage,
        fail_task=fail_task,
        gateway=gw,
        mock=None,
    )


async def run_pipeline_skeleton(task_id: str) -> dict:
    return await run_pipeline(task_id)
