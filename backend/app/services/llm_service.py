"""
============================================================
LLM服务模块 - 增强版（支持缓存、审计、请求头密钥）
应用场景：支持OpenAI/DeepSeek/通义千问/文心一言等
核心功能：服务端不内置任何API密钥，密钥由用户网页保存
创新优化：
  1. 支持浏览器密钥模式（HTTP头发送，不落盘）
  2. SHA256响应缓存（24小时TTL，相同prompt不重复请求）
  3. LLM调用审计日志（记录模型、延迟、成功/失败）
  4. 多厂商动态切换
对应大赛评分点：可自定义大模型API配置、密钥账户隔离存储
============================================================
"""
import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import LLMUserConfig
from app.services.llm_context import get_current_llm_config, LLMRequestConfig


# ==================== 厂商配置 ====================

PROVIDER_DEFAULT_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "ernie-bot": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "moonshot": "https://api.moonshot.cn/v1",
}

PROVIDER_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-v4-pro",
    "qwen": "qwen-plus",
    "ernie-bot": "ernie-speed-pro-128k",
    "glm": "glm-4.7",
    "moonshot": "kimi-k2-instruct",
}

# 各厂商支持的模型列表（供前端下拉选择）— 2026-07-08 联网检索最新模型
PROVIDER_MODELS = {
    "openai": [
        "gpt-5.2", "gpt-5.1", "gpt-5", "gpt-5-mini", "gpt-5-nano",
        "gpt-4.1", "gpt-4.1-mini",
        "gpt-4o", "gpt-4o-mini",
        "o4-mini", "o3", "o3-mini",
    ],
    "deepseek": ["deepseek-v4-pro", "deepseek-v4-flash"],
    "qwen": [
        "qwen3.7-max", "qwen3.7-plus", "qwen3.6-flash",
        "qwen-plus", "qwen-max", "qwen-flash",
        "qwq-plus",
    ],
    "ernie-bot": [
        "ernie-5.1", "ernie-5.0", "ernie-x1.1",
        "ernie-4.5-turbo-128k",
        "ernie-speed-pro-128k", "ernie-lite-pro-128k",
    ],
    "glm": [
        "glm-5.1", "glm-5", "glm-4.7", "glm-4.7-flash", "glm-4.6",
        "glm-4-plus", "glm-4-flash", "glm-4-flashx",
    ],
    "moonshot": [
        "kimi-k2.6", "kimi-k2.7-code", "kimi-k2.7-code-highspeed",
        "kimi-k2-thinking", "kimi-k2-instruct",
    ],
}

# ==================== 响应缓存 ====================

# 内存缓存（Redis不可用时的后备）
_memory_cache: Dict[str, Dict[str, Any]] = {}
# 缓存有效期：24小时
CACHE_TTL = 86400

_redis_conn = None


async def _get_redis():
    """获取Redis连接（懒加载）"""
    global _redis_conn
    if _redis_conn is None:
        try:
            from app.config import settings
            import redis.asyncio as aioredis
            _redis_conn = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True
            )
            await _redis_conn.ping()
        except Exception:
            _redis_conn = None
    return _redis_conn


def _make_cache_key(messages: list, system_prompt: str, model: str, temperature: float) -> str:
    """生成缓存键：对请求内容做SHA256哈希"""
    raw = json.dumps({
        "messages": messages[-5:],  # 只缓存最近5轮对话
        "system_prompt": system_prompt,
        "model": model,
        "temperature": temperature
    }, ensure_ascii=False, sort_keys=True)
    return "llm_cache:" + hashlib.sha256(raw.encode()).hexdigest()


async def _get_cached_response(cache_key: str) -> Optional[Dict[str, Any]]:
    """从缓存获取响应"""
    # 尝试Redis
    redis_conn = await _get_redis()
    if redis_conn:
        try:
            data = await redis_conn.get(cache_key)
            if data:
                return json.loads(data)
        except Exception:
            pass

    # 后备：内存缓存
    cached = _memory_cache.get(cache_key)
    if cached and (time.time() - cached["_cached_at"]) < CACHE_TTL:
        return cached

    return None


async def _set_cached_response(cache_key: str, response: Dict[str, Any]):
    """写入缓存响应"""
    response["_cached_at"] = time.time()

    # 尝试写入Redis
    redis_conn = await _get_redis()
    if redis_conn:
        try:
            await redis_conn.setex(cache_key, CACHE_TTL, json.dumps(response))
            return
        except Exception:
            pass

    # 后备：内存缓存
    _memory_cache[cache_key] = response


# ==================== 审计日志 ====================

async def _log_llm_call(
    db: AsyncSession,
    user_id: int,
    model: str,
    function_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: float,
    success: bool,
    error_message: str = ""
):
    """记录LLM调用日志到数据库"""
    if db is None:
        return
    try:
        from app.models.models import LLMCallLog
        log = LLMCallLog(
            user_id=user_id,
            model=model,
            function_name=function_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message[:500] if error_message else ""
        )
        db.add(log)
        await db.flush()
    except Exception:
        pass  # 审计日志不应影响主流程


# ==================== 核心API函数 ====================

class SimpleLLMConfig:
    """简化的LLM配置对象（兼容DB Config和请求头Config）"""
    def __init__(self,
                 api_key: str = "",
                 base_url: str = "",
                 model_name: str = "",
                 provider: str = "openai",
                 temperature: float = 0.7,
                 max_tokens: int = 4096):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.id = None  # 兼容DB模式


async def _resolve_llm_config(
    db: AsyncSession,
    user_id: int,
    config_id: Optional[int] = None
) -> Optional[SimpleLLMConfig]:
    """
    解析LLM配置（决策顺序）：
    1. 优先使用请求头配置（浏览器密钥模式）
    2. 其次使用指定的config_id
    3. 最后使用用户激活的默认配置
    """
    # 1. 检查请求头中的LLM配置（浏览器密钥模式）
    header_config = get_current_llm_config()
    if header_config and header_config.browser_key_mode and header_config.api_key:
        # 从请求头读取提供商标识，或尝试从base_url推断
        provider = header_config.provider
        if not provider and header_config.base_url:
            for key, url in PROVIDER_DEFAULT_URLS.items():
                if url.rstrip('/') in header_config.base_url.rstrip('/'):
                    provider = key
                    break
        if not provider:
            provider = "openai"

        return SimpleLLMConfig(
            api_key=header_config.api_key,
            base_url=header_config.base_url or PROVIDER_DEFAULT_URLS.get(provider, ""),
            model_name=header_config.model_name or PROVIDER_DEFAULT_MODELS.get(provider, ""),
            provider=provider,
            temperature=header_config.temperature,
            max_tokens=header_config.max_tokens
        )

    # 2. 检查指定的config_id
    if config_id:
        result = await db.execute(
            select(LLMUserConfig)
            .where(LLMUserConfig.id == config_id, LLMUserConfig.user_id == user_id)
        )
        config = result.scalar_one_or_none()
        if config:
            from app.services.crypto_service import decrypt_value
            plain_key = decrypt_value(config.api_key)
            return SimpleLLMConfig(
                api_key=plain_key,
                base_url=config.base_url or PROVIDER_DEFAULT_URLS.get(config.provider, ""),
                model_name=config.model_name or PROVIDER_DEFAULT_MODELS.get(config.provider, ""),
                provider=config.provider,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

    # 3. 使用用户激活的默认配置
    result = await db.execute(
        select(LLMUserConfig)
        .where(LLMUserConfig.user_id == user_id)
        .order_by(LLMUserConfig.is_active.desc(), LLMUserConfig.id.desc())
    )
    config = result.scalar_one_or_none()
    if config:
        from app.services.crypto_service import decrypt_value
        plain_key = decrypt_value(config.api_key)
        return SimpleLLMConfig(
            api_key=plain_key,
            base_url=config.base_url or PROVIDER_DEFAULT_URLS.get(config.provider, ""),
            model_name=config.model_name or PROVIDER_DEFAULT_MODELS.get(config.provider, ""),
            provider=config.provider,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

    return None


def mask_api_key(api_key: str) -> str:
    """对API密钥进行脱敏处理"""
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return api_key[:3] + "***"
    return api_key[:6] + "****" + api_key[-4:]


async def call_llm_api(
    messages: list,
    system_prompt: str = "",
    db: Optional[AsyncSession] = None,
    user_id: int = 0,
    config_id: Optional[int] = None,
    use_cache: bool = True,
    function_name: str = "chat"
) -> Dict[str, Any]:
    """
    调用LLM API的核心函数（增强版）
    - 支持浏览器密钥模式（HTTP头发送密钥）
    - 支持Redis缓存相同请求（24小时TTL）
    - 自动审计日志记录

    Args:
        messages: 对话消息列表
        system_prompt: 系统提示词
        db: 数据库会话（用于审计日志）
        user_id: 用户ID（用于审计日志）
        config_id: 指定配置ID
        use_cache: 是否使用缓存（默认开启）
        function_name: 功能名称（用于审计日志）
    """
    # 解析LLM配置
    config = await _resolve_llm_config(db, user_id, config_id)
    if not config:
        return {
            "success": False,
            "content": "⚠️ 请先在「API配置」页面添加并激活您的LLM API配置，或者在浏览器中保存API密钥后重试。",
            "llm_config_id": None
        }

    base_url = config.base_url
    if not base_url:
        return {"success": False, "error": f"不支持的厂商: {config.provider}", "llm_config_id": None}

    # 构建消息列表
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    # 构建请求数据
    model_name = config.model_name or PROVIDER_DEFAULT_MODELS.get(config.provider, "gpt-4o-mini")
    request_data = {
        "model": model_name,
        "messages": msgs,
        "temperature": config.temperature or 0.7,
        "max_tokens": config.max_tokens or 4096,
    }

    # 生成缓存键
    cache_key = _make_cache_key(messages, system_prompt, model_name, config.temperature)

    # 尝试从缓存获取
    if use_cache:
        cached = await _get_cached_response(cache_key)
        if cached:
            return {**cached, "from_cache": True}

    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}"
    }

    api_url = f"{base_url.rstrip('/')}/chat/completions"
    start_time = time.time()
    elapsed = 0
    success = False
    error_message = ""
    content = ""
    usage = {}

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(api_url, json=request_data, headers=headers)
            elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            success = True
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", response.text)
            except Exception:
                pass
            error_message = f"API请求失败 (HTTP {response.status_code}): {error_detail}"

    except httpx.TimeoutException:
        elapsed = time.time() - start_time
        error_message = "API请求超时，请检查网络连接或API地址"
    except httpx.ConnectError:
        elapsed = time.time() - start_time
        error_message = f"无法连接到 {base_url}，请检查API地址是否正确"
    except Exception as e:
        elapsed = time.time() - start_time
        error_message = f"请求异常: {str(e)}"

    # 构建返回结果
    result_data = {
        "success": success,
        "content": content if success else error_message,
        "usage": usage,
        "response_time_ms": round(elapsed * 1000, 2),
        "llm_config_id": config.id,
        "model": model_name,
        "from_cache": False
    }

    # 写入缓存（仅缓存成功的响应）
    if success and use_cache:
        await _set_cached_response(cache_key, result_data)

    # 记录审计日志（异步不阻塞）
    if db is not None and user_id > 0:
        await _log_llm_call(
            db=db,
            user_id=user_id,
            model=model_name,
            function_name=function_name,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=round(elapsed * 1000, 2),
            success=success,
            error_message=error_message
        )

    return result_data


async def test_llm_connection(
    api_key: str,
    base_url: str,
    model_name: str = "",
    provider: str = "openai"
) -> Dict[str, Any]:
    """
    LLM连通性测试（独立函数，不依赖数据库配置）
    用于前端"一键测试"按钮
    """
    config = SimpleLLMConfig(
        api_key=api_key,
        base_url=base_url or PROVIDER_DEFAULT_URLS.get(provider, ""),
        model_name=model_name or PROVIDER_DEFAULT_MODELS.get(provider, ""),
        provider=provider
    )

    # 临时替换全局config进行测试
    test_messages = [
        {"role": "user", "content": "请回复'连接成功'四个字，不要多余内容。"}
    ]

    base_url_val = config.base_url
    if not base_url_val:
        return {"success": False, "message": "不支持的厂商", "response_time_ms": None}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}"
    }

    model_name_val = config.model_name
    request_data = {
        "model": model_name_val,
        "messages": test_messages,
        "temperature": 0.7,
        "max_tokens": 100,
    }

    api_url = f"{base_url_val.rstrip('/')}/chat/completions"

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=request_data, headers=headers)
            elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "message": f"🎉 API连接成功！（{content[:30]}）",
                "response_time_ms": round(elapsed * 1000, 2)
            }
        else:
            error_detail = response.text
            try:
                error_detail = response.json().get("error", {}).get("message", response.text)
            except Exception:
                pass
            return {
                "success": False,
                "message": f"❌ 连接失败: {error_detail}",
                "response_time_ms": round(elapsed * 1000, 2)
            }

    except httpx.TimeoutException:
        return {"success": False, "message": "❌ 连接超时，请检查API地址", "response_time_ms": None}
    except httpx.ConnectError:
        return {"success": False, "message": f"❌ 无法连接到 {base_url_val}", "response_time_ms": None}
    except Exception as e:
        return {"success": False, "message": f"❌ 连接异常: {str(e)}", "response_time_ms": None}
