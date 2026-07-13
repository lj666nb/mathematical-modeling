"""
============================================================
竞赛训练路由 — 数学建模竞赛 S0-S8 工作流 API
============================================================
端点：
  POST   /api/competition/tasks             创建竞赛任务
  GET    /api/competition/tasks             任务列表
  GET    /api/competition/tasks/{id}        任务详情
  DELETE /api/competition/tasks/{id}        删除任务
  POST   /api/competition/tasks/{id}/upload 上传赛题文件
  GET    /api/competition/tasks/{id}/files  文件列表
  POST   /api/competition/tasks/{id}/preflight  运行 S0 预检
  GET    /api/competition/tasks/{id}/preflight   获取 S0 结果
  POST   /api/competition/tasks/{id}/analyze     运行 S1 赛题分析
  GET    /api/competition/tasks/{id}/analyze      获取 S1 结果
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    CompetitionTaskCreate,
    CompetitionTaskInfo,
    CompetitionTaskDetail,
    CompetitionTaskList,
    PreflightResult,
    AnalysisResult,
    ModelRouteResult,
    DataPipelineResult,
    ModelContractResult,
    EvidenceGateResult,
    PaperResult,
    FormatCheckResult,
)
from app.routers.auth import get_current_user
from app.services.competition_service import CompetitionService

router = APIRouter(prefix="/api/competition", tags=["竞赛训练"])


# ==================== 任务管理 ====================

@router.post("/tasks", response_model=CompetitionTaskInfo)
async def create_task(
    data: CompetitionTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新的竞赛任务"""
    service = CompetitionService(db, current_user.id)
    result = await service.create_task(title=data.title)
    return result


@router.get("/tasks", response_model=CompetitionTaskList)
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的竞赛任务列表"""
    service = CompetitionService(db, current_user.id)
    tasks = await service.list_tasks()
    return CompetitionTaskList(tasks=tasks, total=len(tasks))


@router.get("/tasks/{task_id}", response_model=CompetitionTaskDetail)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取竞赛任务详情（含报告数据）"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除竞赛任务及其所有文件"""
    service = CompetitionService(db, current_user.id)
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已删除", "task_id": task_id}


# ==================== 文件管理 ====================

@router.post("/tasks/{task_id}/upload")
async def upload_files(
    task_id: int,
    files: List[UploadFile] = File(..., description="赛题文件（PDF/DOCX/MD/TXT/CSV/XLSX等）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传赛题文件到指定任务"""
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")

    service = CompetitionService(db, current_user.id)
    try:
        result = await service.upload_files(task_id, files)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tasks/{task_id}/files")
async def list_files(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取任务已上传的文件列表"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    files = await service.get_files(task_id)
    return {"task_id": task_id, "files": files, "count": len(files)}


# ==================== S0 预检 ====================

@router.post("/tasks/{task_id}/preflight", response_model=PreflightResult)
async def run_preflight(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S0 预检：文件分类 + 可读性检查 + 依赖检测 + 附件角色识别

    检查项目：
    - problem_files/ 目录是否存在且非空
    - 题面文件（PDF/DOCX/MD/TXT）是否可提取文本
    - 数据文件（XLSX/CSV/JSON）是否可读
    - 文件名是否疑似结果提交模板（result*.xlsx等）
    - Python依赖（pypdf/python-docx/openpyxl/pandas）是否已安装
    - 是否有旧的final_paper.docx遗留

    产出：preflight_report.json + input_manifest.json
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        result = await service.run_preflight(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预检失败：{str(e)}")


@router.get("/tasks/{task_id}/preflight")
async def get_preflight(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S0 预检结果（从数据库读取）"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    preflight_report = {}
    input_manifest = {}
    try:
        if task["preflight_report"]:
            preflight_report = json.loads(task["preflight_report"])
    except Exception:
        pass
    try:
        if task["input_manifest"]:
            input_manifest = json.loads(task["input_manifest"])
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": preflight_report.get("status", "unknown"),
        "preflight_report": preflight_report,
        "input_manifest": input_manifest,
    }


# ==================== S1 赛题分析 ====================

@router.post("/tasks/{task_id}/analyze", response_model=AnalysisResult)
async def run_analysis(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S1 赛题分析：文本提取 + 子问题拆分 + 任务类型分类 + 模型推荐

    前置条件：S0 预检必须通过（preflight_status == 'pass'）

    分析项目：
    - 从PDF/DOCX/MD/TXT提取完整赛题文本
    - 自动拆分Q1/Q2/Q3...子问题
    - 对每个子问题分类（预测/优化/评价/分类/聚类/机理）
    - 推荐基线模型和改进模型
    - 生成验证计划和建议图表
    - 提取约束条件

    产出：problem_analysis.json + A_题意对齐.md + B_论文大纲.md + C_评分点对齐表.md + D_模型路线.json
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        result = await service.run_analysis(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"赛题分析失败：{str(e)}")


@router.get("/tasks/{task_id}/analyze")
async def get_analysis(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S1 赛题分析结果（从数据库读取）"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    problem_analysis = {}
    questions_count = 0
    task_types: list = []
    try:
        if task["problem_analysis"]:
            problem_analysis = json.loads(task["problem_analysis"])
            questions = problem_analysis.get("questions", [])
            questions_count = len(questions)
            task_types = list(dict.fromkeys(q.get("task_type", "") for q in questions))
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": "completed" if problem_analysis else "not_run",
        "problem_analysis": problem_analysis,
        "questions_count": questions_count,
        "task_types": task_types,
    }


# ==================== S2 模型路线 ====================

@router.post("/tasks/{task_id}/model-route", response_model=ModelRouteResult)
async def run_model_route(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S2 模型路线：模型推荐 + 评分点对齐 + 公式要求 + 图表规划

    前置条件：S1 赛题分析必须已完成（status == 's1_completed'）

    产出：
    - plan/model_route.json：每问的基线模型、主模型、备选模型、公式要求、图表规划、论文落位
    - plan/rubric_alignment.json：评分点→证据形式→论文位置映射
    - plan/scoring_strategy.md：人类可读的评分策略说明
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        result = await service.run_model_route(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型路线生成失败：{str(e)}")


@router.get("/tasks/{task_id}/model-route")
async def get_model_route(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S2 模型路线结果（从数据库读取）"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    model_route = {}
    rubric_alignment = {}
    questions_count = 0
    try:
        if task["model_route"]:
            model_route = json.loads(task["model_route"])
            questions_count = len(model_route.get("questions", []))
    except Exception:
        pass
    try:
        if task["rubric_alignment"]:
            rubric_alignment = json.loads(task["rubric_alignment"])
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": "completed" if model_route else "not_run",
        "model_route": model_route,
        "rubric_alignment": rubric_alignment,
        "questions_count": questions_count,
    }


# ==================== S3-S4 数据处理 + 可视化计划 ====================

@router.post("/tasks/{task_id}/data-pipeline", response_model=DataPipelineResult)
async def run_data_pipeline(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S3-S4 数据处理 + 可视化计划

    前置条件：S2 模型路线必须已完成（status == 's2_completed'）

    产出：
    - plan/data_plan.json：数据画像 + 清洗任务计划 + 问题-字段映射
    - plan/visualization_plan.json：每问图表类型、数据源、坐标轴候选、论文落位
    - figure_index.json：图表索引（规划中/已存在状态追踪）
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        result = await service.run_data_pipeline(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据处理失败：{str(e)}")


@router.get("/tasks/{task_id}/data-pipeline")
async def get_data_pipeline(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S3-S4 数据处理 + 可视化计划结果（从数据库读取）"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    data_plan = {}
    visualization_plan = {}
    data_files_count = 0
    figures_count = 0
    try:
        if task["data_plan"]:
            data_plan = json.loads(task["data_plan"])
            data_files_count = len(data_plan.get("data_files", []))
    except Exception:
        pass
    try:
        if task["visualization_plan"]:
            visualization_plan = json.loads(task["visualization_plan"])
            figures_count = len(visualization_plan.get("figures", []))
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": "completed" if data_plan or visualization_plan else "not_run",
        "data_plan": data_plan,
        "visualization_plan": visualization_plan,
        "data_files_count": data_files_count,
        "figures_count": figures_count,
    }


# ==================== S5 建模代码生成 + 结果契约 ====================

@router.post("/tasks/{task_id}/model-contract", response_model=ModelContractResult)
async def run_model_contract(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S5 建模代码生成 + 结果契约

    前置条件：S3-S4 数据处理必须已完成（status == 's4_completed'）

    产出：
    - results/model_results.json：每问结果摘要 + 参数 + 产出
    - results/metrics.json：每问指标契约
    - results/conclusions.json：每问结论契约
    - tables/table_index.json：表格索引
    - code/modeling/q*_model.py：每问建模代码脚手架
    - code/modeling/result_contract_io.py：工具库
    - code/modeling/run_modeling.py：统一运行入口
    - code/modeling/README.md：工作区说明
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        result = await service.run_model_contract(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建模代码生成失败：{str(e)}")


@router.get("/tasks/{task_id}/model-contract")
async def get_model_contract(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S5 建模代码生成 + 结果契约（从数据库读取）"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    model_contract = {}
    questions_count = 0
    tables_count = 0
    scripts_count = 0
    try:
        if task["model_contract"]:
            model_contract = json.loads(task["model_contract"])
            questions_count = len(model_contract.get("model_results", []))
            tables_count = len(model_contract.get("tables", []))
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": "completed" if model_contract else "not_run",
        "model_contract": model_contract,
        "questions_count": questions_count,
        "tables_count": tables_count,
        "scripts_generated": scripts_count,
    }


# ==================== S6 证据门禁 ====================

@router.post("/tasks/{task_id}/evidence-gate", response_model=EvidenceGateResult)
async def run_evidence_gate(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S6 证据门禁：验证 S0-S5 产出证据完整性

    前置条件：S5 建模代码生成必须已完成（status == 's5_completed'）

    检查项目：
    - 每问是否有模型结果且 evidence_status 合法
    - 每问是否有指标且值非空
    - 每问是否有结论且不依赖占位符
    - 每问是否有表格/图表证据
    - 评分点是否都有对应证据

    产出：evidence_gate.json + evidence_gate_report.json
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        result = await service.run_evidence_gate(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"证据门禁失败：{str(e)}")


@router.get("/tasks/{task_id}/evidence-gate")
async def get_evidence_gate(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S6 证据门禁结果"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    evidence_gate = {}
    total_checks = 0
    passed = 0
    failed = 0
    warnings = 0
    try:
        if task["evidence_gate"]:
            evidence_gate = json.loads(task["evidence_gate"])
            s = evidence_gate.get("summary", {})
            total_checks = s.get("total_checks", 0)
            passed = s.get("passed", 0)
            failed = s.get("failed", 0)
            warnings = s.get("warnings", 0)
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": evidence_gate.get("status", "not_run"),
        "gate_report": evidence_gate,
        "total_checks": total_checks,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
    }


# ==================== S7 论文生成 ====================

@router.post("/tasks/{task_id}/paper-writing", response_model=PaperResult)
async def run_paper_writing(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S7 论文生成：从 S0-S6 全部产出生成完整学术论文草稿

    前置条件：S6 证据门禁必须通过（gate_status == 'PASS'）

    生成论文结构：
    - 标题、摘要、关键词
    - 问题重述
    - 模型建立（分问题）
    - 结果分析（分问题）
    - 模型检验与敏感性分析
    - 结论、参考文献

    产出：draft_paper.md + paper_meta.json
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        result = await service.run_paper_writing(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"论文生成失败：{str(e)}")


@router.get("/tasks/{task_id}/paper-writing")
async def get_paper(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S7 论文草稿内容与元信息"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    paper_meta = {}
    draft_paper = ""
    try:
        if task["draft_paper"]:
            paper_meta = json.loads(task["draft_paper"])
    except Exception:
        pass

    # 尝试从磁盘读取论文全文
    from pathlib import Path
    md_path = Path("paper_output") / str(task_id) / "draft_paper.md"
    if md_path.exists():
        draft_paper = md_path.read_text(encoding="utf-8")

    return {
        "task_id": task_id,
        "status": "completed" if paper_meta else "not_run",
        "paper": paper_meta,
        "draft_paper": draft_paper,
        "sections_count": paper_meta.get("sections_count", 0),
        "word_count": paper_meta.get("word_count", 0),
    }


# ==================== S7 格式门禁 ====================

@router.post("/tasks/{task_id}/format-check", response_model=FormatCheckResult)
async def run_format_check(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    运行 S7 格式门禁：检查论文格式完整性

    前置条件：S7 论文生成必须已完成（status == 's7_completed'）

    检查项目：
    - 字数是否满足最低要求
    - 必需章节是否完整
    - 标题层级是否合理
    - 公式/LaTeX 是否存在
    - 参考文献引用数量
    - 是否残留占位符

    产出：format_check.json
    """
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        result = await service.run_format_check(task_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"格式检查失败：{str(e)}")


@router.get("/tasks/{task_id}/format-check")
async def get_format_check(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 S7 格式检查结果"""
    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    import json
    format_check = {}
    total_checks = 0
    passed = 0
    failed = 0
    try:
        if task["format_check"]:
            format_check = json.loads(task["format_check"])
            s = format_check.get("summary", {})
            total_checks = s.get("total_checks", 0)
            passed = s.get("passed", 0)
            failed = s.get("failed", 0)
    except Exception:
        pass

    return {
        "task_id": task_id,
        "status": format_check.get("status", "not_run"),
        "format_report": format_check,
        "total_checks": total_checks,
        "passed": passed,
        "failed": failed,
    }


# ==================== 论文下载 ====================

@router.get("/tasks/{task_id}/paper/download")
async def download_paper(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    下载论文草稿文件（Markdown 格式）

    返回 paper_output/{task_id}/draft_paper.md
    """
    from pathlib import Path as FilePath

    service = CompetitionService(db, current_user.id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    md_path = FilePath("paper_output") / str(task_id) / "draft_paper.md"
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="论文草稿不存在，请先运行 S7 论文生成")

    return FileResponse(
        path=str(md_path),
        filename=f"paper_task{task_id}.md",
        media_type="text/markdown; charset=utf-8",
    )
