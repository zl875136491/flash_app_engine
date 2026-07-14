"""任务文档序列化与查询辅助。"""

from __future__ import annotations

from beanie import PydanticObjectId

from src.modules.models import Image, Task, User
from src.modules.models.enums import Stage, StageLog, utc_now
from src.modules.tasks.schemas import StageLogOut, TaskDetail, TaskSummary


async def author_itcode(task: Task) -> str:
    author = task.author
    if isinstance(author, User):
        return author.itcode
    # 未 fetch 时尽量解析 Link
    try:
        fetched = await task.author.fetch()  # type: ignore[union-attr]
        if isinstance(fetched, User):
            return fetched.itcode
    except Exception:
        pass
    return "unknown"


async def _image_paths(task: Task) -> list[str]:
    paths: list[str] = []
    for item in task.images or []:
        if isinstance(item, Image):
            paths.append(item.path)
            continue
        try:
            fetched = await item.fetch()  # type: ignore[union-attr]
            if isinstance(fetched, Image):
                paths.append(fetched.path)
        except Exception:
            continue
    return paths


def _logs_out(logs: list[StageLog]) -> list[StageLogOut]:
    return [
        StageLogOut(
            stage=log.stage,
            message=log.message,
            detail=log.detail,
            created_at=log.created_at,
        )
        for log in logs
    ]


async def to_summary(task: Task) -> TaskSummary:
    return TaskSummary(
        id=str(task.id),
        author_itcode=await author_itcode(task),
        raw_voice_text=task.raw_voice_text,
        current_stage=task.current_stage,
        exposed_url=task.exposed_url,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def to_detail(task: Task) -> TaskDetail:
    summary = await to_summary(task)
    return TaskDetail(
        **summary.model_dump(),
        images_content=list(task.images_content or []),
        image_paths=await _image_paths(task),
        logs=_logs_out(list(task.logs or [])),
        allocated_resources=task.allocated_resources,
        generated_code_path=task.generated_code_path,
        containers=list(task.containers or []),
    )


async def get_task_by_id(task_id: str) -> Task | None:
    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        return None
    return await Task.get(oid)


async def list_tasks_for_user(user: User, *, skip: int = 0, limit: int = 50) -> list[Task]:
    limit = max(1, min(limit, 100))
    skip = max(0, skip)
    return (
        await Task.find({"author.$id": user.id})
        .sort(-Task.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )


async def count_tasks_for_user(user: User) -> int:
    return await Task.find({"author.$id": user.id}).count()


async def create_task_document(
    *,
    author: User,
    raw_voice_text: str | None,
    images_content: list[str],
    image_paths: list[str],
) -> Task:
    image_links = []
    for path in image_paths:
        image = Image(path=path, author=author)
        await image.insert()
        image_links.append(image)

    task = Task(
        author=author,
        raw_voice_text=raw_voice_text,
        images=image_links,
        images_content=list(images_content),
    )
    task.append_log(
        stage=Stage.Received,
        message="任务已接收",
        detail="等待异步编排消费",
    )
    # append_log 会再次设置 current_stage；确保时间戳新鲜
    task.created_at = utc_now()
    task.updated_at = utc_now()
    await task.insert()
    return task
