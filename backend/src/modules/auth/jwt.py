"""JWT 签发与校验。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.configs import get_settings


class TokenError(Exception):
    """Token 无效或已过期。"""


def create_access_token(*, itcode: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": itcode,
        "itcode": itcode,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise TokenError("无效或已过期的令牌") from exc

    itcode = payload.get("itcode") or payload.get("sub")
    if not itcode or not isinstance(itcode, str):
        raise TokenError("令牌缺少 itcode")
    payload["itcode"] = itcode
    return payload
