from fastapi import APIRouter

from src.api.asr import router as asr_router
from src.api.auth import router as auth_router
from src.api.health import router as health_router
from src.api.models import router as models_router
from src.api.tasks import router as tasks_router
from src.api.uploads import router as uploads_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(models_router)
api_router.include_router(tasks_router)
api_router.include_router(uploads_router)
api_router.include_router(asr_router)
