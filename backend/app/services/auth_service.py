"""
============================================================
认证服务模块 - 用户注册登录、JWT令牌、密码加密
应用场景：学生/教师/管理员三级权限认证体系
安全增强：JWT密钥环境变量强制、密码强度校验、登录审计
============================================================
"""
import re
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import JWTError, jwt
import bcrypt as _bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.models import User

logger = logging.getLogger("auth_service")


# ============================================================
# JWT 密钥安全校验
# ============================================================

# 已知的不安全默认密钥（硬编码泄露检查）
_INSECURE_KEYS = {
    "ai-tutoring-platform-jwt-secret-key-2024",
    "your-secret-key",
    "change-me",
    "secret",
    "dev-secret-key",
}

_jwt_key_validated = False


def _get_jwt_secret() -> str:
    """获取JWT密钥，含安全性校验"""
    global _jwt_key_validated

    key = settings.JWT_SECRET_KEY
    env_key = os.environ.get("JWT_SECRET_KEY", "")

    # 优先使用环境变量
    effective_key = env_key or key

    if not effective_key:
        raise RuntimeError(
            "⛔ JWT_SECRET_KEY 未配置！\n"
            "   请设置环境变量: export JWT_SECRET_KEY=<your-random-secret>\n"
            "   或创建 .env 文件: JWT_SECRET_KEY=<your-random-secret>"
        )

    if not _jwt_key_validated and effective_key in _INSECURE_KEYS:
        logger.warning(
            "⚠️  WARNING: JWT_SECRET_KEY 使用了已知的不安全默认值！\n"
            "   生产环境请务必更换为随机生成的强密钥。\n"
            "   生成方法: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    _jwt_key_validated = True

    return effective_key


# ============================================================
# 密码策略
# ============================================================

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    校验密码强度
    要求: ≥8字符 + 含数字 + 含字母
    返回 (是否通过, 错误消息)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"密码长度不能少于{settings.PASSWORD_MIN_LENGTH}位"
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"
    if settings.PASSWORD_REQUIRE_LETTER and not re.search(r'[a-zA-Z]', password):
        return False, "密码必须包含至少一个字母"
    return True, ""


def hash_password(password: str) -> str:
    """对密码进行bcrypt哈希加密"""
    password_bytes = password.encode('utf-8')
    salt = _bcrypt.gensalt()
    hashed = _bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码与哈希是否匹配"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return _bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ============================================================
# JWT 令牌
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    令牌中包含用户ID和角色信息，用于身份验证
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    secret = _get_jwt_secret()
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码JWT令牌，验证有效性"""
    try:
        secret = _get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ============================================================
# 用户认证
# ============================================================

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    验证用户登录凭据
    返回用户对象或None
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password_hash):
        return user
    return None


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """根据用户ID获取用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """根据用户名获取用户信息"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


# ============================================================
# 登录审计日志
# ============================================================

async def log_login_attempt(
    db: AsyncSession,
    username: str,
    success: bool,
    ip_address: str = "",
    user_agent: str = "",
    reason: str = ""
):
    """
    记录登录尝试（安全审计）
    失败记录用于检测暴力破解
    """
    try:
        from app.models.models import LLMCallLog  # 复用其审计模式
        # 登录日志记录到应用日志
        status = "SUCCESS" if success else "FAILED"
        extra = f"reason={reason}" if reason else ""
        logger.info(
            f"LOGIN_ATTEMPT | user={username} | status={status} | "
            f"ip={ip_address} | agent={user_agent[:100]} | {extra}"
        )
    except Exception:
        pass


async def get_recent_failed_attempts(db: AsyncSession, username: str, minutes: int = 15) -> int:
    """获取最近N分钟内某个用户的登录失败次数（从应用日志统计，简化实现返回0）"""
    # 生产环境应基于Redis计数器实现
    # 当前简化：由 slowapi 限流替代
    return 0
