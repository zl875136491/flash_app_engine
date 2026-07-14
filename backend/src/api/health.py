from datetime import datetime, timezone

from fastapi import APIRouter

from src.configs import get_settings
from src.core.database import is_db_ready

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    db_ok = is_db_ready()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.app_name,
        "env": settings.app_env,
        "mongodb": "connected" if db_ok else "unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
