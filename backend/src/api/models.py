"""本地模型状态查询 API（只读，便于联调）。"""

from fastapi import APIRouter, HTTPException, status

from src.modules.llm import get_local_model_gateway
from src.modules.llm.errors import LocalModelError

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/status")
async def list_model_status():
    gateway = get_local_model_gateway()
    try:
        return await gateway.status.fetch_status()
    except LocalModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
