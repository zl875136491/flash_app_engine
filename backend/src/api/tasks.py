"""任务 API：创建 / 列表 / 详情 / 额度 / 生命周期。"""

from fastapi import APIRouter, Depends, Query

from src.modules.auth import CurrentUser, get_current_user
from src.modules.tasks import service
from src.modules.tasks.schemas import (
    CreateTaskRequest,
    QuotaOut,
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
    """创建任务并写入 Received 初始日志，随后投递 Celery 编排队列。"""
    return await service.create_task(user, body)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user: CurrentUser = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> TaskListResponse:
    """列出当前用户的任务（按创建时间倒序）。"""
    return await service.list_tasks(user, skip=skip, limit=limit)


@router.get("/quota", response_model=QuotaOut)
async def get_quota(user: CurrentUser = Depends(get_current_user)) -> QuotaOut:
    """当前用户同时运行中的应用额度。"""
    return await service.get_quota(user)


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


@router.post("/{task_id}/stop", response_model=TaskDetail)
async def stop_task(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> TaskDetail:
    """停止运行中的应用（保留记录与数据）。"""
    return await service.stop_task(user, task_id)


@router.post("/{task_id}/start", response_model=TaskDetail)
async def start_task(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> TaskDetail:
    """重新启动已停止的应用（需有空余运行额度）。"""
    return await service.start_task(user, task_id)


@router.post("/{task_id}/retry", response_model=TaskDetail)
async def retry_task(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> TaskDetail:
    """失败任务重新进入编排流水线。"""
    return await service.retry_task(user, task_id)


@router.delete("/{task_id}")
async def remove_task(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """移除应用：删除容器并删除任务记录。"""
    return await service.remove_task(user, task_id)
