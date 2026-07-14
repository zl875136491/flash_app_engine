"""用户仓储：按 ITCode 查询 / 幂等创建。"""

from __future__ import annotations

from src.modules.models.enums import utc_now
from src.modules.models.user import User


async def get_user_by_itcode(itcode: str) -> User | None:
    return await User.find_one(User.itcode == itcode)


async def get_or_create_user(*, itcode: str, name: str | None = None) -> User:
    """登录成功后写入/复用 User 文档。"""
    existing = await get_user_by_itcode(itcode)
    if existing is not None:
        return existing

    user = User(itcode=itcode, name=name or itcode)
    await user.insert()
    return user


async def ensure_user_updated_name(user: User, name: str) -> User:
    if user.name != name:
        user.name = name
        user.updated_at = utc_now()
        await user.save()
    return user
