from fastapi import APIRouter

from src.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)

# 后续任务点挂载：
# - auth (任务点 2)
# - tasks (任务点 5)
