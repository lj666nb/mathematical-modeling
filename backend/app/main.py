"""
============================================================
主入口模块 - FastAPI 应用启动文件
应用场景：AI多智能体 × 数学建模智能教学平台
安全增强：slowapi限流、JWT密钥校验、API密钥加密存储
============================================================
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import redis.asyncio as aioredis
import os

from app.config import settings
from app.database import init_database, close_database
from app.routers import auth, llm_config, experiments, practice, chat, teacher, competition, knowledge, code_executor, workspace, profile
from app.services.llm_context import LLMHeaderMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库"""
    print("🚀 AI数学建模智能教学平台启动中...")

    # 校验JWT密钥安全性
    from app.services.auth_service import _get_jwt_secret
    try:
        _get_jwt_secret()
        print("✅ JWT密钥校验通过")
    except RuntimeError as e:
        print(f"⛔ {e}")
        raise

    await init_database()
    yield
    await close_database()
    print("👋 应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI多智能体 × 数学建模智能教学平台",
    lifespan=lifespan
)

# 注册 slowapi 限流异常处理器
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 中间件配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM请求头解析中间件（浏览器密钥模式支持）
app.add_middleware(LLMHeaderMiddleware)

# 注册路由
app.include_router(auth.router)
app.include_router(llm_config.router)
app.include_router(experiments.router)
app.include_router(practice.router)
app.include_router(chat.router)
app.include_router(teacher.router)
app.include_router(competition.router)
app.include_router(knowledge.router)
app.include_router(code_executor.router)
app.include_router(workspace.router)
app.include_router(profile.router)


@app.get("/api/health")
async def health_check():
    """健康检查接口 — 供 Docker / Nginx / 监控使用"""
    health = {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

    # 检查 Redis 连通性
    try:
        redis_client = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            socket_connect_timeout=2
        )
        await redis_client.ping()
        await redis_client.close()
        health["redis"] = "connected"
    except Exception:
        health["redis"] = "unavailable"

    # 检查数据库连通性
    try:
        from sqlalchemy import text
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception:
        health["database"] = "unavailable"

    return health


@app.get("/")
async def root():
    """根路径重定向"""
    return {
        "message": "AI数学建模智能教学平台 API 服务",
        "docs": "/docs",
        "health": "/api/health"
    }
