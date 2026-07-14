"""认证相关 Pydantic schema。"""

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    itcode: str = Field(..., min_length=1, max_length=64, description="用户 ITCode")

    @field_validator("itcode")
    @classmethod
    def normalize_itcode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("itcode 不能为空")
        return normalized


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    itcode: str
    expires_in: int = Field(..., description="令牌有效期（秒）")


class CurrentUser(BaseModel):
    itcode: str
    name: str

    @classmethod
    def from_itcode(cls, itcode: str) -> "CurrentUser":
        # 任务点 3 接入 User 文档后可补充真实姓名；当前以 itcode 作为展示名
        return cls(itcode=itcode, name=itcode)
