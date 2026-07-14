"""任务 API：创建 / 列表 / 详情 / 阶段日志。"""

from fastapi import APIRouter, Depends, Query

from src.modules.auth import CurrentUser, get_current_user
from src.modules.tasks import service
from src.modules.tasks.schemas import (
    CreateTaskRequest,
    StageLogOut,
    TaskDetail,
    TaskListResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskDetail, status_code=201)
async def create_task(
    body: CreateTaskRequest,
    user: CurrentUser = Depends(get_current_user),
) -> TaskDetail:
    """创建任务并写入 Received 初始日志。异步编排将在任务点 6 接入。"""
    return await service.create_task(user, body)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user: CurrentUser = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> TaskListResponse:
    """列出当前用户的任务（按创建时间倒序）。"""
    return await service.list_tasks(user, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> TaskDetail:
    """获取任务详情（仅本人可见）。"""
    return await service.get_task(user, task_id)


@router.get("/{task_id}/logs", response_model=list[StageLogOut])
async def get_task_logs(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> list[StageLogOut]:
    """获取任务阶段日志流。"""
    return await service.get_task_logs(user, task_id)
