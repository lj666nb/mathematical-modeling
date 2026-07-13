"""
============================================================
个人中心路由 — 学习记录 + 论文管理 + 统计仪表盘
PRF-001/002/003/004
============================================================
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.models import User, AgentChat, PracticeRecord, CompetitionTask
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["个人中心"])


@router.get("/records")
async def get_learning_records(
    type: str = Query(default="all", description="记录类型: all/chat/practice"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学习记录列表（对话历史 + 练习记录）"""
    records = []

    if type in ("all", "chat"):
        chat_result = await db.execute(
            select(AgentChat)
            .where(AgentChat.user_id == current_user.id)
            .order_by(desc(AgentChat.created_at))
            .limit(page_size)
        )
        for chat in chat_result.scalars().all():
            records.append({
                "id": f"chat-{chat.id}",
                "type": "chat",
                "agent_type": chat.agent_type,
                "title": f"{_agent_label(chat.agent_type)}对话",
                "detail": (chat.user_message or "")[:100],
                "created_at": chat.created_at.isoformat() if chat.created_at else "",
            })

    if type in ("all", "practice"):
        prac_result = await db.execute(
            select(PracticeRecord)
            .where(PracticeRecord.user_id == current_user.id)
            .order_by(desc(PracticeRecord.completed_at))
            .limit(page_size)
        )
        for pr in prac_result.scalars().all():
            records.append({
                "id": f"practice-{pr.id}",
                "type": "practice",
                "title": f"练习 #{pr.experiment_id}",
                "detail": f"得分: {pr.score or 0}",
                "created_at": pr.completed_at.isoformat() if pr.completed_at else "",
            })

    # 按时间排序取前N
    records.sort(key=lambda r: r["created_at"], reverse=True)
    records = records[:page_size]

    return {"records": records, "total": len(records)}


@router.get("/papers")
async def get_paper_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取历史论文列表（竞赛任务）"""
    result = await db.execute(
        select(CompetitionTask)
        .where(CompetitionTask.user_id == current_user.id)
        .order_by(desc(CompetitionTask.updated_at))
        .limit(page_size)
    )
    tasks = result.scalars().all()

    papers = []
    for t in tasks:
        has_paper = bool(t.draft_paper)
        papers.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "current_step": t.current_step,
            "file_count": t.file_count,
            "has_paper": has_paper,
            "created_at": t.created_at.isoformat() if t.created_at else "",
            "updated_at": t.updated_at.isoformat() if t.updated_at else "",
        })

    return {"papers": papers, "total": len(papers)}


@router.get("/stats")
async def get_learning_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学习统计数据（PRF-004 学习仪表盘）"""
    # 对话统计
    chat_count_result = await db.execute(
        select(func.count(AgentChat.id))
        .where(AgentChat.user_id == current_user.id)
    )
    total_chats = chat_count_result.scalar() or 0

    # 按Agent类型统计
    agent_stats_result = await db.execute(
        select(AgentChat.agent_type, func.count(AgentChat.id))
        .where(AgentChat.user_id == current_user.id)
        .group_by(AgentChat.agent_type)
    )
    agent_counts = {row[0]: row[1] for row in agent_stats_result.all()}

    # 练习统计
    prac_count_result = await db.execute(
        select(func.count(PracticeRecord.id))
        .where(PracticeRecord.user_id == current_user.id)
    )
    total_practices = prac_count_result.stat() or 0

    avg_score_result = await db.execute(
        select(func.avg(PracticeRecord.score))
        .where(PracticeRecord.user_id == current_user.id)
    )
    avg_score = round(avg_score_result.scalar() or 0, 1)

    # 竞赛统计
    task_count_result = await db.execute(
        select(func.count(CompetitionTask.id))
        .where(CompetitionTask.user_id == current_user.id)
    )
    total_tasks = task_count_result.scalar() or 0

    # 各阶段任务数
    completed_tasks_result = await db.execute(
        select(func.count(CompetitionTask.id))
        .where(
            CompetitionTask.user_id == current_user.id,
            CompetitionTask.status.in_(["s7_completed", "s7_check_passed"]),
        )
    )
    completed_tasks = completed_tasks_result.scalar() or 0

    return {
        "total_chats": total_chats,
        "agent_breakdown": {
            "code-review": agent_counts.get("code-review", 0),
            "training-guide": agent_counts.get("training-guide", 0),
            "qa": agent_counts.get("qa", 0),
            "paper-review": agent_counts.get("paper-review", 0),
        },
        "total_practices": total_practices,
        "avg_practice_score": avg_score,
        "total_competition_tasks": total_tasks,
        "completed_tasks": completed_tasks,
    }


def _agent_label(agent_type: str) -> str:
    mapping = {
        "code-review": "建模辅导",
        "training-guide": "实训引导",
        "qa": "建模答疑",
        "paper-review": "论文评审",
    }
    return mapping.get(agent_type, agent_type)
