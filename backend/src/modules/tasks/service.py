"""任务业务逻辑。"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.configs import get_settings
from src.core.database import is_db_ready
from src.modules.auth.schemas import CurrentUser
from src.modules.models import get_or_create_user, get_user_by_itcode
from src.modules.models.enums import Stage, utc_now
from src.modules.sandbox.lifecycle import (
    remove_task_runtime,
    start_task_runtime,
    stop_task_runtime,
)
from src.modules.tasks import repo
from src.modules.tasks.schemas import (
    CreateTaskRequest,
    QuotaOut,
    StageLogOut,
    TaskDetail,
    TaskListResponse,
    TaskSummary,
)
from src.modules.worker import enqueue_process_task


def require_db() -> None:
    if not is_db_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="数据库不可用，无法操作任务",
        )


async def _author_or_404(user: CurrentUser):
    author = await get_user_by_itcode(user.itcode)
    if author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return author


async def _owned_task_or_404(user: CurrentUser, task_id: str):
    task = await repo.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    author_code = await repo.author_itcode(task)
    if author_code != user.itcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


async def get_quota(user: CurrentUser) -> QuotaOut:
    require_db()
    settings = get_settings()
    limit = max(1, settings.user_app_running_limit)
    author = await get_user_by_itcode(user.itcode)
    used = 0 if author is None else await repo.count_running_tasks_for_user(author)
    return QuotaOut(limit=limit, used=used, remaining=max(0, limit - used))


async def ensure_running_slot(user: CurrentUser, *, action: str = "操作") -> None:
    """若运行中额度已满则抛 409。"""
    quota = await get_quota(user)
    if quota.remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"同时运行中的应用已达上限（{quota.used}/{quota.limit}），"
                f"请先停止或移除一个后再{action}"
            ),
        )


async def create_task(user: CurrentUser, body: CreateTaskRequest) -> TaskDetail:
    require_db()
    await ensure_running_slot(user, action="创建")
    author = await get_or_create_user(itcode=user.itcode, name=user.name)
    task = await repo.create_task_document(
        author=author,
        raw_voice_text=body.raw_voice_text,
        images_content=body.images_content,
        image_paths=body.image_paths,
    )

    settings = get_settings()
    if settings.celery_task_always_eager:
        # 开发冒烟：同进程内联执行骨架流水线，不经过 broker
        from src.modules.worker.pipeline import run_pipeline_skeleton

        task.append_log(
            stage=Stage.Received,
            message="已投递异步编排队列",
            detail="celery_id=eager-inline",
        )
        task.updated_at = utc_now()
        await task.save()
        await run_pipeline_skeleton(str(task.id))
    else:
        celery_id = enqueue_process_task(str(task.id))
        if celery_id is None:
            task.append_log(
                stage=Stage.Received,
                message="异步入队失败",
                detail="Celery broker 不可用，任务已落库，可稍后由 Worker 补偿消费",
            )
        else:
            task.append_log(
                stage=Stage.Received,
                message="已投递异步编排队列",
                detail=f"celery_id={celery_id}",
            )
        task.updated_at = utc_now()
        await task.save()

    refreshed = await repo.get_task_by_id(str(task.id))
    return await repo.to_detail(refreshed or task)


async def list_tasks(
    user: CurrentUser,
    *,
    skip: int = 0,
    limit: int = 50,
) -> TaskListResponse:
    require_db()
    author = await get_user_by_itcode(user.itcode)
    quota = await get_quota(user)
    if author is None:
        return TaskListResponse(items=[], total=0, quota=quota)

    tasks = await repo.list_tasks_for_user(author, skip=skip, limit=limit)
    total = await repo.count_tasks_for_user(author)
    items: list[TaskSummary] = [await repo.to_summary(t) for t in tasks]
    return TaskListResponse(items=items, total=total, quota=quota)


async def get_task(user: CurrentUser, task_id: str) -> TaskDetail:
    require_db()
    task = await _owned_task_or_404(user, task_id)
    return await repo.to_detail(task)


async def get_task_logs(user: CurrentUser, task_id: str) -> list[StageLogOut]:
    detail = await get_task(user, task_id)
    return detail.logs


async def stop_task(user: CurrentUser, task_id: str) -> TaskDetail:
    require_db()
    task = await _owned_task_or_404(user, task_id)
    if task.current_stage != Stage.Success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="仅运行中（已部署）的应用可以停止",
        )

    result = stop_task_runtime(task)
    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止失败：{result.detail}",
        )

    task.append_log(
        stage=Stage.Stopped,
        message="应用已停止",
        detail=result.detail[:2000],
    )
    task.updated_at = utc_now()
    await task.save()
    return await repo.to_detail(task)


async def start_task(user: CurrentUser, task_id: str) -> TaskDetail:
    require_db()
    task = await _owned_task_or_404(user, task_id)
    if task.current_stage != Stage.Stopped:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="仅已停止的应用可以启动",
        )

    await ensure_running_slot(user, action="启动")
    result = start_task_runtime(task)
    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动失败：{result.detail}",
        )

    if result.containers is not None:
        task.containers = result.containers
    if result.exposed_url:
        task.exposed_url = result.exposed_url

    task.append_log(
        stage=Stage.Success,
        message="应用已重新启动",
        detail=f"{result.detail}; url={task.exposed_url}",
    )
    task.updated_at = utc_now()
    await task.save()
    return await repo.to_detail(task)


async def remove_task(user: CurrentUser, task_id: str) -> dict:
    require_db()
    task = await _owned_task_or_404(user, task_id)
    # 进行中任务不允许直接删，避免与 Worker 竞态
    if task.current_stage in {
        Stage.Received,
        Stage.Analyzing,
        Stage.Coding,
        Stage.Building,
        Stage.Verifying,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="编排进行中的任务暂不可移除，请等待完成或失败后再操作",
        )

    result = remove_task_runtime(task)
    await task.delete()
    return {"ok": True, "task_id": task_id, "detail": result.detail}


async def retry_task(user: CurrentUser, task_id: str) -> TaskDetail:
    require_db()
    task = await _owned_task_or_404(user, task_id)
    if task.current_stage != Stage.Failed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="仅失败状态的任务可以重试",
        )

    await ensure_running_slot(user, action="重试")

    # 清理可能残留的失败运行时，重新编排
    remove_task_runtime(task)
    task.containers = []
    task.exposed_url = None
    task.generated_code_path = None
    task.append_log(
        stage=Stage.Received,
        message="用户触发失败重试",
        detail="重新进入编排流水线",
    )
    task.updated_at = utc_now()
    await task.save()

    settings = get_settings()
    if settings.celery_task_always_eager:
        from src.modules.worker.pipeline import run_pipeline_skeleton

        await run_pipeline_skeleton(str(task.id))
    else:
        celery_id = enqueue_process_task(str(task.id))
        task.append_log(
            stage=Stage.Received,
            message="已投递异步编排队列",
            detail=f"celery_id={celery_id or 'unavailable'}",
        )
        task.updated_at = utc_now()
        await task.save()

    refreshed = await repo.get_task_by_id(str(task.id))
    return await repo.to_detail(refreshed or task)
