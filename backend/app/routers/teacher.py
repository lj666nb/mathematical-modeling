"""
============================================================
教师端数据统计路由
应用场景：教师查看班级实训数据统计、学生成绩分析
对应大赛评分点：教师端实训数据统计看板
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.models import User, PracticeRecord, Experiment
from app.schemas.schemas import TeacherStats
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/teacher", tags=["教师端"])


@router.get("/stats", response_model=TeacherStats)
async def get_teacher_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取教师端统计数据（仅教师和管理员可访问）"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="仅教师和管理员可查看统计数据")

    # 学生总数
    student_count = await db.execute(
        select(func.count()).where(User.role == "student")
    )
    total_students = student_count.scalar() or 0

    # 总实训记录数
    record_count = await db.execute(select(func.count()).select_from(PracticeRecord))
    total_records = record_count.scalar() or 0

    # 平均分
    avg_score = await db.execute(
        select(func.avg(PracticeRecord.score)).where(PracticeRecord.status == "evaluated")
    )
    average_score = round(avg_score.scalar() or 0, 1)

    # 学科分布统计
    subject_dist = await db.execute(
        select(Experiment.subject, func.count(PracticeRecord.id))
        .join(PracticeRecord, Experiment.id == PracticeRecord.experiment_id, isouter=True)
        .group_by(Experiment.subject)
    )
    subject_distribution = [
        {"subject": row[0], "count": row[1]}
        for row in subject_dist.all()
    ]

    # 分数段分布
    score_ranges = [
        ("90-100", 90, 100),
        ("80-89", 80, 89),
        ("70-79", 70, 79),
        ("60-69", 60, 69),
        ("60以下", 0, 59),
    ]
    score_distribution = []
    for label, low, high in score_ranges:
        count_row = await db.execute(
            select(func.count())
            .where(
                PracticeRecord.score >= low,
                PracticeRecord.score <= high,
                PracticeRecord.status == "evaluated"
            )
        )
        score_distribution.append({
            "range": label,
            "count": count_row.scalar() or 0
        })

    # 优秀学生排行（前10）
    top_query = (
        select(
            User.display_name,
            User.class_name,
            func.avg(PracticeRecord.score).label("avg_score"),
            func.count(PracticeRecord.id).label("total_practices")
        )
        .join(PracticeRecord, User.id == PracticeRecord.user_id)
        .where(
            User.role == "student",
            PracticeRecord.status == "evaluated"
        )
        .group_by(User.id)
        .order_by(desc("avg_score"))
        .limit(10)
    )
    top_result = await db.execute(top_query)
    top_students = [
        {
            "name": row.display_name or row.class_name or "未知",
            "class_name": row.class_name or "",
            "avg_score": round(row.avg_score, 1) if row.avg_score else 0,
            "total_practices": row.total_practices
        }
        for row in top_result.all()
    ]

    return TeacherStats(
        total_students=total_students,
        total_records=total_records,
        average_score=average_score,
        subject_distribution=subject_distribution,
        score_distribution=score_distribution,
        top_students=top_students
    )
