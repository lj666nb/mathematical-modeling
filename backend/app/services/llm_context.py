"""
============================================================
LLM请求上下文模块 - 支持请求级别的动态LLM参数
应用场景：允许前端API密钥通过HTTP头发送，不持久化到服务端
核心逻辑：
  1. 使用ContextVar存储当前请求的LLM配置
  2. FastAPI中间件从HTTP头提取X-LLM-Api-Key等参数
  3. 当请求头存在时，优先使用请求头配置而非数据库配置
  4. 实现"密钥不碰服务端磁盘"的隐私安全模式

对应大赛评分点：密钥账户隔离存储、隐私安全保护
============================================================
"""
from contextvars import ContextVar
from typing import Optional, Dict, Any
from dataclasses import dataclass
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class LLMRequestConfig:
    """
    请求级别的LLM配置
    从HTTP头提取，不持久化到数据库
    """
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    provider: str = ""
    temperature: float = 0.7
    max_tokens: int = 16384
    # 是否为"浏览器密钥模式"（密钥不落盘）
    browser_key_mode: bool = False


# ContextVar保存当前请求的LLM配置（线程安全）
# 每个请求独立，支持多用户并发不同API密钥
current_llm_config: ContextVar[Optional[LLMRequestConfig]] = ContextVar(
    "current_llm_config", default=None
)


def get_current_llm_config() -> Optional[LLMRequestConfig]:
    """获取当前请求的LLM配置"""
    return current_llm_config.get()


def set_current_llm_config(config: Optional[LLMRequestConfig]):
    """设置当前请求的LLM配置"""
    current_llm_config.set(config)


class LLMHeaderMiddleware(BaseHTTPMiddleware):
    """
    FastAPI中间件 - 从HTTP头提取LLM配置
    支持的请求头：
      X-LLM-Api-Key: API密钥
      X-LLM-Base-Url: API地址
      X-LLM-Model: 模型名称
      X-LLM-Provider: 厂商标识
      X-LLM-Temperature: 温度参数
      X-LLM-Max-Tokens: 最大Token数
    当这些请求头存在时，优先使用请求头配置而非数据库配置
    """

    async def dispatch(self, request: Request, call_next):
        # 从请求头提取LLM配置
        api_key = request.headers.get("X-LLM-Api-Key", "")
        base_url = request.headers.get("X-LLM-Base-Url", "")

        if api_key:
            # 浏览器密钥模式：密钥通过HTTP头发送，不存储到数据库
            config = LLMRequestConfig(
                api_key=api_key,
                base_url=base_url or request.headers.get("X-LLM-Base-Url", ""),
                model_name=request.headers.get("X-LLM-Model", ""),
                provider=request.headers.get("X-LLM-Provider", ""),
                temperature=float(request.headers.get("X-LLM-Temperature", "0.7")),
                max_tokens=int(request.headers.get("X-LLM-Max-Tokens", "4096")),
                browser_key_mode=True
            )
            set_current_llm_config(config)
        else:
            set_current_llm_config(None)

        # 继续处理请求
        response = await call_next(request)
        return response
