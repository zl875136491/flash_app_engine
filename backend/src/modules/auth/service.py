"""ITCode 登录与鉴权业务逻辑。"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.configs import get_settings
from src.core.database import is_db_ready
from src.modules.auth.allowlist import is_allowed_itcode
from src.modules.auth.jwt import create_access_token
from src.modules.auth.schemas import LoginRequest, TokenResponse


async def login_with_itcode(body: LoginRequest) -> TokenResponse:
    if not is_allowed_itcode(body.itcode):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ITCode 不存在或未授权",
        )

    # Mongo 可用时幂等写入 User，供后续 Task.author Link 使用
    if is_db_ready():
        from src.modules.models import get_or_create_user

        await get_or_create_user(itcode=body.itcode, name=body.itcode)

    settings = get_settings()
    token = create_access_token(itcode=body.itcode)
    return TokenResponse(
        access_token=token,
        itcode=body.itcode,
        expires_in=settings.jwt_expire_minutes * 60,
    )
