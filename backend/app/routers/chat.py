"""
============================================================
智能体对话路由 - AI多智能体交互接口
应用场景：调用代码纠错/实训引导/专业课答疑三大Agent
对应大赛评分点：多智能体对话交互、上下文管理
============================================================
"""
import uuid
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional

from app.database import get_db
from app.models.models import AgentChat, User
from app.schemas.schemas import (
    AgentChatRequest, AgentChatResponse, ChatHistoryInfo, ChatHistoryList,
    ChatRatingRequest, FileUploadResponse
)
from app.routers.auth import get_current_user
from app.agents.dispatcher import AgentDispatcher
from app.services.pdf_utils import extract_pdf_text
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["AI智能体对话"])


async def _get_chat_redis():
    """获取 Redis 连接（用于聊天文件上下文缓存）"""
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT,
            db=settings.REDIS_DB, password=settings.REDIS_PASSWORD or None,
            decode_responses=True
        )
        await r.ping()
        return r
    except Exception:
        return None


@router.post("/send", response_model=AgentChatResponse)
async def send_message(
    data: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    向AI智能体发送消息，获取回复
    通过调度中心统一分发到对应Agent处理
    """
    # 验证智能体类型
    valid_agents = ["code-review", "training-guide", "qa", "paper-review", "general"]
    if data.agent_type not in valid_agents:
        raise HTTPException(status_code=400, detail=f"无效的智能体类型，可选: {', '.join(valid_agents)}")

    # 生成或使用已有会话ID
    session_id = data.session_id or str(uuid.uuid4())

    # 从 Redis 加载当前会话附加的文件上下文
    file_context = None
    redis_conn = await _get_chat_redis()
    if redis_conn:
        try:
            raw = await redis_conn.get(f"chat_file:{current_user.id}:{session_id}")
            if raw:
                file_info = json.loads(raw)
                file_context = file_info.get("full_text", "")
        except Exception:
            pass

    # 通过智能体调度中心处理请求
    dispatcher = AgentDispatcher(db, current_user.id)
    result = await dispatcher.dispatch(
        agent_type=data.agent_type,
        message=data.message,
        session_id=session_id,
        llm_config_id=data.llm_config_id,
        code_context=data.code_context,
        file_context=file_context
    )

    # 保存对话记录到数据库
    chat = AgentChat(
        user_id=current_user.id,
        agent_type=data.agent_type,
        session_id=session_id,
        llm_config_id=result.get("llm_config_id"),
        user_message=data.message,
        agent_message=result.get("content", ""),
        extra_metadata=result.get("metadata", "{}")
    )
    db.add(chat)
    await db.flush()
    await db.refresh(chat)

    return AgentChatResponse(
        session_id=session_id,
        agent_type=data.agent_type,
        user_message=data.message,
        agent_message=result.get("content", ""),
        chat_id=chat.id
    )


# ==================== SSE 流式对话接口 ====================
# 通过Server-Sent Events实时流式传输AI智能体的回复
# 前端使用EventSource或fetch ReadableStream接收

@router.post("/stream")
async def chat_stream(
    data: AgentChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    SSE流式对话接口
    与send_message功能相同，但通过Server-Sent Events流式返回AI回复
    前端可以逐token显示AI输出，提升交互体验
    """
    # 验证智能体类型
    valid_agents = ["code-review", "training-guide", "qa", "paper-review", "general"]
    if data.agent_type not in valid_agents:
        raise HTTPException(status_code=400, detail=f"无效的智能体类型")

    session_id = data.session_id or str(uuid.uuid4())
    full_content = ""

    # 从 Redis 加载文件上下文
    file_context = None
    redis_conn = await _get_chat_redis()
    if redis_conn:
        try:
            raw = await redis_conn.get(f"chat_file:{current_user.id}:{session_id}")
            if raw:
                file_info = json.loads(raw)
                file_context = file_info.get("full_text", "")
        except Exception:
            pass

    async def generate():
        nonlocal full_content

        # 通过调度中心处理请求（非流式，但我们可以流式返回结果）
        from app.agents.dispatcher import AgentDispatcher
        dispatcher = AgentDispatcher(db, current_user.id)

        # 发送开始事件
        yield f"event: start\ndata: {json.dumps({'session_id': session_id})}\n\n"

        result = await dispatcher.dispatch(
            agent_type=data.agent_type,
            message=data.message,
            session_id=session_id,
            llm_config_id=data.llm_config_id,
            code_context=data.code_context,
            file_context=file_context
        )

        if result.get("success"):
            content = result.get("content", "")
            full_content = content
            # 分块发送内容（每块约50字符）
            chunk_size = 50
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.02)  # 模拟打字效果
        else:
            yield f"data: {json.dumps({'type': 'error', 'content': result.get('content', 'AI服务暂不可用')})}\n\n"

        # 保存对话记录
        try:
            chat = AgentChat(
                user_id=current_user.id,
                agent_type=data.agent_type,
                session_id=session_id,
                llm_config_id=result.get("llm_config_id"),
                user_message=data.message,
                agent_message=full_content,
                extra_metadata=result.get("metadata", "{}")
            )
            db.add(chat)
            await db.commit()
        except Exception:
            pass

        # 发送完成事件（包含 chat_id 供前端评分使用）
        chat_id = chat.id if chat else None
        yield f"event: done\ndata: {json.dumps({'type': 'done', 'session_id': session_id, 'chat_id': chat_id, 'content': full_content})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history", response_model=ChatHistoryList)
async def get_chat_history(
    session_id: Optional[str] = Query(None, description="会话ID"),
    agent_type: Optional[str] = Query(None, description="智能体类型筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话历史记录"""
    base_query = select(AgentChat).where(AgentChat.user_id == current_user.id)

    if session_id:
        base_query = base_query.where(AgentChat.session_id == session_id)
    if agent_type:
        base_query = base_query.where(AgentChat.agent_type == agent_type)

    base_query = base_query.order_by(desc(AgentChat.created_at))

    # 获取总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = base_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    chats = result.scalars().all()

    # 获取会话列表
    sessions_query = (
        select(AgentChat.session_id, AgentChat.agent_type, func.max(AgentChat.created_at).label("last_time"))
        .where(AgentChat.user_id == current_user.id)
        .group_by(AgentChat.session_id, AgentChat.agent_type)
        .order_by(desc("last_time"))
        .limit(50)
    )
    sessions_result = await db.execute(sessions_query)
    sessions = [
        {
            "session_id": s.session_id,
            "agent_type": s.agent_type,
            "last_time": s.last_time.isoformat() if s.last_time else ""
        }
        for s in sessions_result.all()
    ]

    return ChatHistoryList(
        sessions=sessions,
        history=[ChatHistoryInfo.model_validate(c) for c in chats],
        total=total
    )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除指定会话记录"""
    result = await db.execute(
        select(AgentChat).where(
            AgentChat.session_id == session_id,
            AgentChat.user_id == current_user.id
        )
    )
    chats = result.scalars().all()
    for chat in chats:
        await db.delete(chat)
    return {"message": f"已删除 {len(chats)} 条对话记录", "session_id": session_id}


@router.post("/{chat_id}/rate")
async def rate_message(
    chat_id: int,
    data: ChatRatingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """对 Agent 回复进行满意度评分（赞/踩）"""
    result = await db.execute(
        select(AgentChat).where(
            AgentChat.id == chat_id,
            AgentChat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="对话记录不存在")

    # 存储评分到 metadata JSON 字段
    import json
    try:
        meta = json.loads(chat.extra_metadata) if chat.extra_metadata else {}
    except (json.JSONDecodeError, TypeError):
        meta = {}
    meta["rating"] = data.rating
    chat.extra_metadata = json.dumps(meta, ensure_ascii=False)
    db.add(chat)
    await db.flush()

    return {"chat_id": chat_id, "rating": data.rating, "message": "评分已记录"}


# ==================== 文件上传与上下文管理 ====================


@router.post("/upload-file", response_model=FileUploadResponse)
async def upload_chat_file(
    session_id: str = Form(..., description="会话ID"),
    file: UploadFile = File(..., description="PDF 文件"),
    current_user: User = Depends(get_current_user),
):
    """
    上传 PDF 文件到聊天会话
    - 提取 PDF 文本内容
    - 存入 Redis（会话级缓存，自动过期）
    - 后续消息自动附带文件上下文
    """
    # 1. 校验文件类型
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    # 2. 保存到磁盘
    dir_path = Path(f"paper_output/chat_files/{current_user.id}/{session_id}")
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    # 3. 提取文本
    full_text = extract_pdf_text(file_path)
    if not full_text.strip():
        raise HTTPException(status_code=400, detail="无法从 PDF 中提取文本内容（可能是扫描版 PDF）")

    # 截断超长文本（保留前 100000 字符）
    if len(full_text) > 100000:
        full_text = full_text[:100000] + "\n\n...(内容已截断)"

    text_preview = full_text[:300]

    # 4. 存入 Redis
    redis_conn = await _get_chat_redis()
    if redis_conn:
        try:
            await redis_conn.setex(
                f"chat_file:{current_user.id}:{session_id}",
                settings.SESSION_TIMEOUT,
                json.dumps({
                    "filename": file.filename,
                    "full_text": full_text,
                    "text_preview": text_preview,
                    "char_count": len(full_text)
                }, ensure_ascii=False)
            )
        except Exception:
            pass  # Redis 不可用不影响上传成功

    return FileUploadResponse(
        filename=file.filename,
        text_preview=text_preview,
        char_count=len(full_text),
        session_id=session_id,
    )


@router.delete("/session/{session_id}/file")
async def clear_chat_file(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """清除聊天会话中附加的文件"""
    redis_conn = await _get_chat_redis()
    if redis_conn:
        try:
            await redis_conn.delete(f"chat_file:{current_user.id}:{session_id}")
        except Exception:
            pass
    return {"message": "文件已清除", "session_id": session_id}
