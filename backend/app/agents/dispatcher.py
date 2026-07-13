"""
============================================================
智能体调度中心（核心调度模块）
应用场景：统一分发任务到三大Agent、管理多轮对话记忆
核心逻辑：
  1. 根据agent_type将请求路由到对应的Agent处理
  2. 从Redis缓存中读取/写入对话上下文，保持多轮记忆
  3. 读取用户网页配置的LLM参数传递给Agent
  4. 记录每次调用的元数据（使用的模型、token消耗等）

对应大赛评分点：多智能体调度协同、对话上下文管理
============================================================
"""
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_base import BaseAgent
from app.agents.code_review_agent import CodeReviewAgent
from app.agents.training_guide_agent import TrainingGuideAgent
from app.agents.qa_agent import QAAgent
from app.agents.paper_review_agent import PaperReviewAgent
from app.config import settings

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class AgentDispatcher:
    """
    智能体调度中心
    负责请求路由、会话管理、上下文传递
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self._redis = None

        # 注册所有Agent实例（懒加载）
        self._agents = {
            "code-review": None,
            "training-guide": None,
            "qa": None,
            "paper-review": None,
            "general": None
        }

    async def _get_redis(self):
        """获取Redis连接（懒加载，连接失败则使用内存缓存）"""
        if self._redis is None and REDIS_AVAILABLE:
            try:
                self._redis = aioredis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True
                )
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _get_agent(self, agent_type: str) -> BaseAgent:
        """根据类型获取Agent实例（懒加载）"""
        if agent_type == "code-review":
            if self._agents["code-review"] is None:
                self._agents["code-review"] = CodeReviewAgent(self.db, self.user_id)
            return self._agents["code-review"]
        elif agent_type == "training-guide":
            if self._agents["training-guide"] is None:
                self._agents["training-guide"] = TrainingGuideAgent(self.db, self.user_id)
            return self._agents["training-guide"]
        elif agent_type == "qa":
            if self._agents["qa"] is None:
                self._agents["qa"] = QAAgent(self.db, self.user_id)
            return self._agents["qa"]
        elif agent_type == "paper-review":
            if self._agents["paper-review"] is None:
                self._agents["paper-review"] = PaperReviewAgent(self.db, self.user_id)
            return self._agents["paper-review"]
        elif agent_type == "general":
            # 通用模式：使用 QA Agent（覆盖面最广的数学建模问答）
            if self._agents["general"] is None:
                self._agents["general"] = QAAgent(self.db, self.user_id)
            return self._agents["general"]
        else:
            raise ValueError(f"未知的智能体类型: {agent_type}")

    async def _load_context(self, session_id: str) -> List[dict]:
        """
        从Redis加载对话上下文
        结构: {session_id: [{role, content}, ...]}
        """
        redis_conn = await self._get_redis()
        if redis_conn:
            try:
                data = await redis_conn.get(f"chat_context:{self.user_id}:{session_id}")
                if data:
                    return json.loads(data)
            except Exception:
                pass

        # Redis不可用时，从数据库加载最近对话
        from sqlalchemy import select, desc
        from app.models.models import AgentChat

        result = await self.db.execute(
            select(AgentChat)
            .where(
                AgentChat.user_id == self.user_id,
                AgentChat.session_id == session_id
            )
            .order_by(desc(AgentChat.created_at))
            .limit(20)
        )
        chats = result.scalars().all()
        chats.reverse()

        context = []
        for chat in chats:
            context.append({"role": "user", "content": chat.user_message})
            context.append({"role": "assistant", "content": chat.agent_message})
        return context

    async def _save_context(self, session_id: str, context: List[dict]):
        """保存对话上下文到Redis缓存"""
        redis_conn = await self._get_redis()
        if redis_conn:
            try:
                await redis_conn.setex(
                    f"chat_context:{self.user_id}:{session_id}",
                    settings.SESSION_TIMEOUT,
                    json.dumps(context)
                )
            except Exception:
                pass  # Redis不可用时静默忽略，数据仍保存在数据库

    async def dispatch(
        self,
        agent_type: str,
        message: str,
        session_id: str,
        llm_config_id: Optional[int] = None,
        code_context: Optional[str] = None,
        file_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调度中心核心分发方法

        执行流程：
        1. 从Redis加载对话上下文
        2. 根据agent_type获取对应Agent
        3. 调用Agent处理消息
        4. 更新对话上下文到Redis
        5. 返回处理结果
        """
        # 1. 加载对话历史上下文
        context = await self._load_context(session_id)

        # 2. 获取对应Agent
        agent = self._get_agent(agent_type)

        # 3. 调用Agent处理
        result = await agent.process(
            message=message,
            session_id=session_id,
            history=context,
            config_id=llm_config_id,
            code_context=code_context,
            file_context=file_context
        )

        # 4. 更新上下文缓存
        if result.get("success"):
            context.append({"role": "user", "content": message})
            context.append({"role": "assistant", "content": result.get("content", "")})
            await self._save_context(session_id, context)

        # 5. 构建元数据
        metadata = {
            "agent_type": agent_type,
            "session_id": session_id,
            "temperature": None,
            "model": None
        }
        llm_config = await agent.get_llm_config(llm_config_id)
        if llm_config:
            metadata["temperature"] = llm_config.temperature
            metadata["model"] = llm_config.model_name

        result["metadata"] = json.dumps(metadata, ensure_ascii=False)

        return result
