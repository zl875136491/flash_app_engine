"""任务业务逻辑。"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.core.database import is_db_ready
from src.modules.auth.schemas import CurrentUser
from src.modules.models import get_or_create_user, get_user_by_itcode
from src.modules.models.enums import Stage, utc_now
from src.modules.tasks import repo
from src.modules.tasks.schemas import (
    CreateTaskRequest,
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


async def create_task(user: CurrentUser, body: CreateTaskRequest) -> TaskDetail:
    require_db()
    author = await get_or_create_user(itcode=user.itcode, name=user.name)
    task = await repo.create_task_document(
        author=author,
        raw_voice_text=body.raw_voice_text,
        images_content=body.images_content,
        image_paths=body.image_paths,
    )

    from src.configs import get_settings

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
    if author is None:
        return TaskListResponse(items=[], total=0)

    tasks = await repo.list_tasks_for_user(author, skip=skip, limit=limit)
    total = await repo.count_tasks_for_user(author)
    items: list[TaskSummary] = [await repo.to_summary(t) for t in tasks]
    return TaskListResponse(items=items, total=total)


async def get_task(user: CurrentUser, task_id: str) -> TaskDetail:
    require_db()
    task = await repo.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    author_code = await repo.author_itcode(task)
    if author_code != user.itcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    return await repo.to_detail(task)


async def get_task_logs(user: CurrentUser, task_id: str) -> list[StageLogOut]:
    detail = await get_task(user, task_id)
    return detail.logs
