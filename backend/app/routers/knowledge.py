"""
============================================================
知识库路由 — 数学建模 8 大分类 + 学习路径
============================================================
"""
from fastapi import APIRouter, Query
from typing import Optional

from app.services.knowledge_service import (
    get_all_categories,
    get_category,
    search_knowledge,
    get_learning_paths,
    get_all_cases,
    get_case_detail,
    get_all_exams,
    get_exam_detail,
)

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/categories")
async def list_categories():
    """获取所有模型分类摘要（8大分类）"""
    return {"categories": get_all_categories(), "total": 8}


@router.get("/categories/{category_id}")
async def get_category_detail(category_id: str):
    """获取单个分类的完整知识（定义/公式/场景/例题/算法）"""
    from fastapi import HTTPException

    cat = get_category(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail=f"分类不存在: {category_id}")
    return cat


@router.get("/search")
async def search(q: str = Query(..., min_length=1, description="搜索关键词")):
    """全文搜索知识库"""
    results = search_knowledge(q)
    return {"query": q, "results": results, "total": len(results)}


@router.get("/learning-paths")
async def learning_paths():
    """获取学习路径推荐（新手→进阶→竞赛）"""
    return {"paths": get_learning_paths()}


@router.get("/cases")
async def list_cases():
    """获取案例库摘要列表（历年竞赛优秀论文解析）"""
    cases = get_all_cases()
    return {"cases": cases, "total": len(cases)}


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """获取单个案例的完整解析"""
    from fastapi import HTTPException

    case = get_case_detail(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"案例不存在: {case_id}")
    return case


@router.get("/exams")
async def list_exams():
    """获取历年真题库摘要列表"""
    exams = get_all_exams()
    return {"exams": exams, "total": len(exams)}


@router.get("/exams/{exam_id}")
async def get_exam(exam_id: str):
    """获取单个真题的完整信息"""
    from fastapi import HTTPException

    exam = get_exam_detail(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail=f"真题不存在: {exam_id}")
    return exam
