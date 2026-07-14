from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)

# 后续任务点挂载：
# - tasks (任务点 5)
