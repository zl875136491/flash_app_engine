"""任务业务逻辑。"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.core.database import is_db_ready
from src.modules.auth.schemas import CurrentUser
from src.modules.models import get_or_create_user, get_user_by_itcode
from src.modules.tasks import repo
from src.modules.tasks.schemas import (
    CreateTaskRequest,
    StageLogOut,
    TaskDetail,
    TaskListResponse,
    TaskSummary,
)


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
    return await repo.to_detail(task)


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
