"""
============================================================
LLM API配置管理路由 - 大赛核心创新功能
应用场景：可视化面板配置多厂商大模型API、密钥隔离存储
核心逻辑：每个登录用户独立配置自有密钥，服务端不内置任何密钥
安全增强：API密钥Fernet加密存储，返回时脱敏，浏览器密钥模式零存储
对应大赛评分点：自定义大模型API配置、密钥账号隔离存储
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as delete_stmt
from typing import List

from app.database import get_db
from app.models.models import LLMUserConfig
from app.schemas.schemas import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigInfo, LLMTestRequest, LLMTestResult
)
from pydantic import BaseModel, Field
from app.routers.auth import get_current_user
from app.models.models import User
from app.services.llm_service import (
    mask_api_key, test_llm_connection, PROVIDER_DEFAULT_URLS, PROVIDER_DEFAULT_MODELS, PROVIDER_MODELS
)
from app.services.crypto_service import encrypt_value, decrypt_value

router = APIRouter(prefix="/api/llm-config", tags=["LLM API配置"])


@router.get("/providers")
async def get_providers():
    """获取支持的厂商列表（供前端表单选择）"""
    return {
        "providers": [
            {"key": "openai", "name": "OpenAI", "default_url": "https://api.openai.com/v1", "models": PROVIDER_MODELS.get("openai", [])},
            {"key": "deepseek", "name": "DeepSeek", "default_url": "https://api.deepseek.com/v1", "models": PROVIDER_MODELS.get("deepseek", [])},
            {"key": "qwen", "name": "通义千问", "default_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "models": PROVIDER_MODELS.get("qwen", [])},
            {"key": "ernie-bot", "name": "文心一言", "default_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat", "models": PROVIDER_MODELS.get("ernie-bot", [])},
            {"key": "glm", "name": "智谱GLM", "default_url": "https://open.bigmodel.cn/api/paas/v4", "models": PROVIDER_MODELS.get("glm", [])},
            {"key": "moonshot", "name": "Moonshot", "default_url": "https://api.moonshot.cn/v1", "models": PROVIDER_MODELS.get("moonshot", [])},
        ]
    }


async def get_llm_config_by_id(db: AsyncSession, config_id: int, user_id: int):
    """获取用户指定的LLM配置"""
    result = await db.execute(
        select(LLMUserConfig)
        .where(LLMUserConfig.id == config_id, LLMUserConfig.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("/create", response_model=LLMConfigInfo)
async def create_config(
    data: LLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新的LLM API配置（API密钥加密存储）"""
    # 加密API密钥后存储
    encrypted_key = encrypt_value(data.api_key)

    config = LLMUserConfig(
        user_id=current_user.id,
        config_name=data.config_name,
        provider=data.provider,
        api_key=encrypted_key,
        base_url=data.base_url,
        model_name=data.model_name,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        is_active=1
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)

    # 返回时脱敏API密钥（用原始明文密钥脱敏）
    result = LLMConfigInfo.model_validate(config)
    result.api_key = mask_api_key(data.api_key)
    return result


@router.get("/list", response_model=List[LLMConfigInfo])
async def list_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的所有LLM API配置列表（密钥脱敏返回）"""
    result = await db.execute(
        select(LLMUserConfig)
        .where(LLMUserConfig.user_id == current_user.id)
        .order_by(LLMUserConfig.id.desc())
    )
    configs = result.scalars().all()

    # 脱敏API密钥（先解密再脱敏）
    config_list = []
    for config in configs:
        c = LLMConfigInfo.model_validate(config)
        try:
            plain_key = decrypt_value(config.api_key)
            c.api_key = mask_api_key(plain_key)
        except Exception:
            c.api_key = "****"  # 解密失败时仅显示占位符
        config_list.append(c)
    return config_list


@router.get("/{config_id}", response_model=LLMConfigInfo)
async def get_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个LLM配置详情（密钥脱敏返回）"""
    config = await get_llm_config_by_id(db, config_id, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    result = LLMConfigInfo.model_validate(config)
    try:
        plain_key = decrypt_value(config.api_key)
        result.api_key = mask_api_key(plain_key)
    except Exception:
        result.api_key = "****"
    return result


@router.put("/{config_id}", response_model=LLMConfigInfo)
async def update_config(
    config_id: int,
    data: LLMConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新LLM配置（API密钥变更时重新加密）"""
    config = await get_llm_config_by_id(db, config_id, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 逐字段更新
    update_data = data.model_dump(exclude_unset=True)

    # 如果更新了api_key，先加密再存储
    if "api_key" in update_data and update_data["api_key"]:
        new_plain_key = update_data["api_key"]
        update_data["api_key"] = encrypt_value(new_plain_key)
        plain_key_for_mask = new_plain_key
    else:
        try:
            plain_key_for_mask = decrypt_value(config.api_key)
        except Exception:
            plain_key_for_mask = config.api_key

    for key, value in update_data.items():
        setattr(config, key, value)

    db.add(config)
    await db.flush()
    await db.refresh(config)

    result = LLMConfigInfo.model_validate(config)
    result.api_key = mask_api_key(plain_key_for_mask)
    return result


@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除LLM配置"""
    config = await get_llm_config_by_id(db, config_id, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    await db.delete(config)
    return {"message": "配置已删除", "id": config_id}


@router.post("/test", response_model=LLMTestResult)
async def test_config(
    data: LLMTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    一键测试LLM API连通性（自动解密密钥后测试）
    """
    config = await get_llm_config_by_id(db, data.config_id, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 解密存储的API密钥
    plain_key = decrypt_value(config.api_key)
    if plain_key.startswith("[DECRYPTION"):
        raise HTTPException(status_code=500, detail="API密钥解密失败，请重新配置")

    result = await test_llm_connection(
        api_key=plain_key,
        base_url=config.base_url or PROVIDER_DEFAULT_URLS.get(config.provider, ""),
        model_name=config.model_name or PROVIDER_DEFAULT_MODELS.get(config.provider, ""),
        provider=config.provider
    )
    return LLMTestResult(
        success=result["success"],
        message=result["message"],
        response_time_ms=result.get("response_time_ms")
    )


class LLMRawTestRequest(BaseModel):
    """原始连通性测试请求（不依赖数据库配置）"""
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(default="", description="API地址")
    model_name: str = Field(default="", description="模型名称")
    provider: str = Field(default="openai", description="厂商")


@router.post("/test-raw", response_model=LLMTestResult)
async def test_raw_config(data: LLMRawTestRequest):
    """
    原始API连通性测试（不依赖数据库存储的配置）
    用于浏览器密钥模式下的连通性验证
    密钥仅通过请求传输，不存储到服务器
    """
    result = await test_llm_connection(
        api_key=data.api_key,
        base_url=data.base_url or PROVIDER_DEFAULT_URLS.get(data.provider, ""),
        model_name=data.model_name or PROVIDER_DEFAULT_MODELS.get(data.provider, ""),
        provider=data.provider
    )
    return LLMTestResult(
        success=result["success"],
        message=result["message"],
        response_time_ms=result.get("response_time_ms")
    )
