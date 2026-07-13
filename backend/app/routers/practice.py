"""
============================================================
实训记录路由 - 代码提交、AI评分、历史记录
应用场景：学生在线编写代码提交实验，AI智能体自动评分反馈
对应大赛评分点：实训过程记录、AI辅助评分
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional

from app.database import get_db
from app.models.models import PracticeRecord, Experiment, User
from app.schemas.schemas import PracticeSubmit, PracticeRecordInfo, PracticeList
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/practice", tags=["实训记录"])


@router.post("/submit", response_model=PracticeRecordInfo)
async def submit_practice(
    data: PracticeSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交实训代码（学生提交代码后由AI评分）"""
    # 检查实验是否存在
    result = await db.execute(select(Experiment).where(Experiment.id == data.experiment_id))
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验题目不存在")

    # 创建实训记录（AI评测将在后台异步完成或由前端触发）
    record = PracticeRecord(
        user_id=current_user.id,
        experiment_id=data.experiment_id,
        submitted_code=data.code,
        language=data.language,
        status="submitted"
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return PracticeRecordInfo(
        id=record.id,
        user_id=record.user_id,
        experiment_id=record.experiment_id,
        experiment_title=experiment.title,
        subject=experiment.subject,
        submitted_code=record.submitted_code,
        language=record.language,
        score=record.score,
        feedback=record.feedback,
        status=record.status,
        completed_at=record.completed_at
    )


@router.get("/records", response_model=PracticeList)
async def get_practice_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的实训记录列表"""
    query = (
        select(PracticeRecord, Experiment.title, Experiment.subject)
        .join(Experiment, PracticeRecord.experiment_id == Experiment.id)
        .where(PracticeRecord.user_id == current_user.id)
        .order_by(desc(PracticeRecord.completed_at))
    )

    count_query = select(func.count()).select_from(
        select(PracticeRecord)
        .where(PracticeRecord.user_id == current_user.id)
        .subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    records = []
    for row in rows:
        record, title, subject = row
        records.append(PracticeRecordInfo(
            id=record.id,
            user_id=record.user_id,
            experiment_id=record.experiment_id,
            experiment_title=title,
            subject=subject,
            submitted_code=record.submitted_code,
            language=record.language,
            score=record.score,
            feedback=record.feedback,
            status=record.status,
            completed_at=record.completed_at
        ))

    return PracticeList(records=records, total=total)


@router.get("/records/{record_id}", response_model=PracticeRecordInfo)
async def get_practice_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取实训记录详情"""
    result = await db.execute(
        select(PracticeRecord, Experiment.title, Experiment.subject)
        .join(Experiment, PracticeRecord.experiment_id == Experiment.id)
        .where(PracticeRecord.id == record_id, PracticeRecord.user_id == current_user.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="实训记录不存在")

    record, title, subject = row
    return PracticeRecordInfo(
        id=record.id,
        user_id=record.user_id,
        experiment_id=record.experiment_id,
        experiment_title=title,
        subject=subject,
        submitted_code=record.submitted_code,
        language=record.language,
        score=record.score,
        feedback=record.feedback,
        status=record.status,
        completed_at=record.completed_at
    )
