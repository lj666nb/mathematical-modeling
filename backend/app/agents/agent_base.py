"""
============================================================
AI智能体基类 - 增强版
应用场景：所有AI Agent的抽象基类，定义统一接口
核心逻辑：从用户网页配置读取LLM参数，调用多厂商API
优化（来自Edu-TA/Education-Agent项目经验）：
  1. 支持浏览器密钥模式（HTTP头发送密钥）
  2. Redis缓存机制减少重复API调用
  3. LLM调用审计日志
  4. 结构化输出支持
============================================================
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import LLMUserConfig
from app.services.llm_service import call_llm_api, _resolve_llm_config, PROVIDER_DEFAULT_URLS, PROVIDER_DEFAULT_MODELS


class BaseAgent(ABC):
    """
    AI智能体基类
    所有Agent继承此类，实现统一的处理接口
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self._config: Optional[LLMUserConfig] = None

    @abstractmethod
    async def process(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        处理用户消息的抽象方法
        子类必须实现此方法
        """
        pass

    async def get_llm_config(self, config_id: Optional[int] = None) -> Optional[dict]:
        """获取当前有效的LLM配置信息"""
        config = await _resolve_llm_config(self.db, self.user_id, config_id)
        return config

    async def call_llm(
        self,
        messages: List[dict],
        system_prompt: str = "",
        config_id: Optional[int] = None,
        use_cache: bool = True,
        function_name: str = "agent_chat"
    ) -> Dict[str, Any]:
        """
        调用LLM API的统一方法（增强版）
        - 自动读取用户网页配置或浏览器密钥
        - 支持Redis缓存相同请求
        - 自动记录审计日志

        Args:
            messages: 对话消息列表
            system_prompt: 系统提示词
            config_id: 指定LLM配置ID
            use_cache: 是否启用缓存
            function_name: 功能名称（审计用）
        """
        result = await call_llm_api(
            messages=messages,
            system_prompt=system_prompt,
            db=self.db,
            user_id=self.user_id,
            config_id=config_id,
            use_cache=use_cache,
            function_name=function_name
        )

        if not result.get("success") and not result.get("content", "").startswith("⚠️"):
            # 错误时补充提示信息
            result["content"] = f"⚠️ AI服务暂不可用: {result.get('content', '未知错误')}\n\n请检查：\n1. API密钥是否正确\n2. API地址是否可访问\n3. 账户余额是否充足"

        return result

    def build_context_messages(
        self,
        message: str,
        history: Optional[List[dict]] = None
    ) -> List[dict]:
        """构建带历史上下文的对话消息列表"""
        messages = []
        if history:
            messages.extend(history[-10:])  # 保留最近10轮对话
        messages.append({"role": "user", "content": message})
        return messages
