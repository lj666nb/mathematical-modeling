"""
============================================================
配置模块 - AI多智能体 × 数学建模教学平台
应用场景：全局配置管理，支持环境变量覆盖
============================================================
"""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "AI-Tutoring Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置（SQLite文件路径）
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/tutoring.db"

    # Redis 配置（容器内通过服务名连接）
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # JWT 认证配置
    # ⚠️ SECURITY: 生产环境必须通过环境变量注入，无默认值则拒绝启动
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 876000  # 100年，永久有效

    # 数据加密密钥（用于API密钥等敏感字段的DB静态加密）
    # ⚠️ 生产环境必须通过环境变量注入，开发环境自动生成并持久化到 data/.encryption_key
    DATA_ENCRYPTION_KEY: str = ""

    # 密码强度配置
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_REQUIRE_DIGIT: bool = False
    PASSWORD_REQUIRE_LETTER: bool = False

    # 登录安全配置
    LOGIN_RATE_LIMIT: str = "5/minute"  # 登录接口限流
    MAX_LOGIN_ATTEMPTS: int = 10         # 最大连续失败次数

    # 密码加密配置
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"

    # 会话超时（秒）
    SESSION_TIMEOUT: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
