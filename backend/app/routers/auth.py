"""
============================================================
用户认证路由 - 注册、登录、个人信息管理
应用场景：学生/教师/管理员三级权限体系
安全增强：密码强度校验、登录限流、审计日志
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    UserRegister, UserLogin, UserInfo, TokenResponse, UserProfileUpdate, PasswordChange
)
from app.services.auth_service import (
    hash_password, authenticate_user, create_access_token,
    get_user_by_id, decode_access_token, validate_password_strength,
    log_login_attempt
)

router = APIRouter(prefix="/api/auth", tags=["用户认证"])
security = HTTPBearer()

# 限流器：登录接口 5次/分钟/IP
limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前登录用户（依赖注入）"""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的令牌载荷")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册接口"""
    from sqlalchemy import select

    # 密码强度校验
    valid, msg = validate_password_strength(data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 验证角色合法性（普通用户不可注册为admin）
    if data.role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="无效的用户角色")

    # 创建新用户
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        class_name=data.class_name,
        display_name=data.display_name or data.username
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # 生成JWT令牌
    token = create_access_token({"user_id": user.id, "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserInfo.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口
    限流: 5次/分钟/IP (防暴力破解)
    """
    client_ip = get_remote_address(request)
    user_agent = request.headers.get("User-Agent", "")

    user = await authenticate_user(db, data.username, data.password)
    if not user:
        await log_login_attempt(
            db, data.username, success=False,
            ip_address=client_ip, user_agent=user_agent,
            reason="invalid_credentials"
        )
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    # 记录登录成功
    await log_login_attempt(
        db, data.username, success=True,
        ip_address=client_ip, user_agent=user_agent
    )

    # 生成JWT令牌
    token = create_access_token({"user_id": user.id, "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserInfo.model_validate(user)
    )


@router.get("/check-username")
async def check_username(username: str, db: AsyncSession = Depends(get_db)):
    """检查用户名是否已被注册（注册页实时校验用）"""
    from app.services.auth_service import get_user_by_username
    user = await get_user_by_username(db, username)
    return {"exists": user is not None}


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserInfo.model_validate(current_user)


@router.put("/profile")
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人资料（昵称、班级）"""
    if data.display_name:
        current_user.display_name = data.display_name
    # class_name 可以为空字符串（清空班级）
    current_user.class_name = data.class_name
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return UserInfo.model_validate(current_user)


@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    from app.services.auth_service import verify_password

    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    current_user.password_hash = hash_password(data.new_password)
    db.add(current_user)
    return {"message": "密码修改成功"}


@router.post("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """验证令牌是否有效"""
    return {"valid": True, "user_id": current_user.id, "role": current_user.role}
