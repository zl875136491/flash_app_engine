"""认证 API：ITCode 登录、当前用户信息。"""

from fastapi import APIRouter, Depends

from src.modules.auth.deps import get_current_user
from src.modules.auth.schemas import CurrentUser, LoginRequest, TokenResponse
from src.modules.auth.service import login_with_itcode

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """核验 ITCode 存在性后签发 JWT。无需密码。"""
    return await login_with_itcode(body)


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """返回当前令牌对应用户；同时作为鉴权中间件的示例接口。"""
    return user
