"""FastAPI 鉴权依赖。"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.modules.auth.allowlist import is_allowed_itcode
from src.modules.auth.jwt import TokenError, decode_access_token
from src.modules.auth.schemas import CurrentUser

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    itcode = payload["itcode"]
    if not is_allowed_itcode(itcode):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不在授权名单中",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser.from_itcode(itcode)
