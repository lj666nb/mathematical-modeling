"""
============================================================
实验题库管理路由 - 数学建模分类题库
应用场景：优化模型/预测模型/评价模型/分类与聚类/微分方程/统计模型/图论与网络/随机模型
对应大赛评分点：模型分类题库、实验题目管理
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.models import Experiment
from app.schemas.schemas import ExperimentInfo, ExperimentList
from app.routers.auth import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/experiments", tags=["实验题库"])


@router.get("/subjects")
async def get_subjects():
    """获取所有学科分类"""
    return {
        "subjects": ["优化模型", "预测模型", "评价模型", "分类与聚类", "微分方程", "统计模型", "图论与网络", "随机模型"]
    }


@router.get("/list", response_model=ExperimentList)
async def list_experiments(
    subject: Optional[str] = Query(None, description="学科分类筛选"),
    difficulty: Optional[int] = Query(None, description="难度筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取实验题库列表（支持按学科分类筛选）"""
    query = select(Experiment)

    if subject:
        query = query.where(Experiment.subject == subject)
    if difficulty:
        query = query.where(Experiment.difficulty == difficulty)

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(Experiment.subject, Experiment.difficulty, Experiment.id)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    experiments = result.scalars().all()

    return ExperimentList(
        experiments=[ExperimentInfo.model_validate(e) for e in experiments],
        total=total
    )


@router.get("/{experiment_id}", response_model=ExperimentInfo)
async def get_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取单个实验题目详情"""
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验题目不存在")
    return ExperimentInfo.model_validate(experiment)
