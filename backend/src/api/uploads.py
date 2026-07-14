"""图片上传：供任务创建时写入 image_paths。"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.configs import get_settings
from src.modules.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
}


class UploadImageResponse(BaseModel):
    path: str = Field(..., description="宿主机保存路径，可写入 Task.image_paths")
    filename: str
    content_type: str | None = None
    size: int


@router.post("/images", response_model=UploadImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
) -> UploadImageResponse:
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片类型: {content_type}",
        )

    settings = get_settings()
    upload_root = Path(settings.upload_root) / user.itcode
    upload_root.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}:
        suffix = ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = upload_root / filename

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="空文件")
    if len(data) > settings.upload_max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="图片过大")

    target.write_bytes(data)
    return UploadImageResponse(
        path=str(target),
        filename=filename,
        content_type=file.content_type,
        size=len(data),
    )
