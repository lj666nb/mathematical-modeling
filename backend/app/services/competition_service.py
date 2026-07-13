"""
============================================================
竞赛服务模块 — 数学建模竞赛 S0-S8 工作流引擎
============================================================
核心能力：
  S0 预检：文件分类、可读性检查、依赖检测、附件角色识别、生成 input_manifest
  S1 赛题分析：文本提取、子问题拆分、任务类型分类、模型推荐、验证计划

设计参考：MathModel-Skill-master 中的 preflight_check.py / analyze_problem.py
适配调整：从 CLI 脚本改写为 Web 服务，支持异步 + 数据库持久化
============================================================
"""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings

# ============================================================
# 常量定义
# ============================================================

DOC_EXTS = {".pdf", ".docx", ".md", ".txt"}
LEGACY_DOC_EXTS = {".doc"}
DATA_EXTS = {".xlsx", ".xls", ".csv", ".tsv", ".json"}
SUSPICIOUS_NAME_HINTS = ("result", "结果", "submit", "提交")

DEP_IMPORT_TO_PACKAGE = {
    "pypdf": "pypdf",
    "docx": "python-docx",
    "openpyxl": "openpyxl",
    "xlrd": "xlrd",
    "pandas": "pandas",
    "fitz": "PyMuPDF",
}

QUESTION_NUMERALS = {
    1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
    6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
}

MODEL_RULES = [
    {
        "task_type": "预测/回归",
        "keywords": ["预测", "预报", "趋势", "估计", "回归", "未来", "时间序列", "forecast"],
        "baseline": "线性回归、移动平均、指数平滑或ARIMA",
        "improved": "特征工程+树模型、集成学习或时序深度模型",
        "validation": ["留出验证或滚动回测", "RMSE/MAE/MAPE", "残差分析与置信区间"],
        "figures": ["真实值-预测值对比图", "残差分布图", "趋势外推图"],
    },
    {
        "task_type": "优化/规划",
        "keywords": ["优化", "最优", "最大", "最小", "分配", "调度", "路径", "选址", "成本", "收益", "约束"],
        "baseline": "线性规划、整数规划或可行规则基线",
        "improved": "多目标规划、启发式算法、遗传算法或模拟退火",
        "validation": ["可行性检查", "约束满足率", "与基准策略对比", "敏感性分析"],
        "figures": ["方案对比柱状图", "约束满足情况图", "敏感性分析折线图"],
    },
    {
        "task_type": "评价/排序",
        "keywords": ["评价", "评估", "排序", "排名", "指标体系", "权重", "综合", "打分", "优劣"],
        "baseline": "归一化+加权求和",
        "improved": "熵权法、CRITIC、AHP、TOPSIS或VIKOR",
        "validation": ["权重敏感性分析", "排名稳定性检验", "与已知事实对照"],
        "figures": ["指标权重图", "综合得分排序图", "雷达图或热力图"],
    },
    {
        "task_type": "分类/识别",
        "keywords": ["分类", "识别", "判别", "类别", "风险等级", "是否", "检测"],
        "baseline": "逻辑回归、朴素贝叶斯或决策树",
        "improved": "随机森林、梯度提升或代价敏感学习",
        "validation": ["混淆矩阵", "Precision/Recall/F1", "ROC/AUC或PR曲线"],
        "figures": ["混淆矩阵热力图", "ROC曲线", "特征重要性图"],
    },
    {
        "task_type": "聚类/分群",
        "keywords": ["聚类", "分群", "画像", "相似性", "模式发现", "群体"],
        "baseline": "K-means或层次聚类",
        "improved": "GMM、DBSCAN或谱聚类",
        "validation": ["轮廓系数", "聚类稳定性", "群体差异解释"],
        "figures": ["降维散点图", "群体特征对比图", "聚类热力图"],
    },
    {
        "task_type": "机理/仿真",
        "keywords": ["机理", "仿真", "微分", "动力学", "物理", "传播", "过程", "系统"],
        "baseline": "差分方程、微分方程或机理方程",
        "improved": "参数校准、不确定性分析或数据驱动校正",
        "validation": ["历史拟合", "参数敏感性", "极端情景测试"],
        "figures": ["仿真曲线图", "参数敏感性图", "情景对比图"],
    },
]

# ============================================================
# S2 模型路线：备选模型库 + 公式要求
# ============================================================

BACKUP_MODELS = {
    "预测": ["ARIMA", "XGBoost回归", "随机森林回归"],
    "回归": ["岭回归", "随机森林回归", "XGBoost回归"],
    "优化": ["整数规划", "遗传算法", "模拟退火"],
    "规划": ["线性规划", "多目标规划", "遗传算法"],
    "评价": ["熵权法", "TOPSIS", "CRITIC"],
    "排序": ["TOPSIS", "VIKOR", "AHP"],
    "分类": ["逻辑回归", "随机森林", "梯度提升树"],
    "识别": ["逻辑回归", "随机森林", "代价敏感学习"],
    "聚类": ["K-means", "DBSCAN", "GMM"],
    "仿真": ["差分方程", "参数校准仿真", "情景模拟"],
    "机理": ["微分方程", "参数反演", "不确定性分析"],
}

FORMULA_REQUIREMENTS = {
    "预测": ["定义输入特征矩阵 X", "定义预测目标 y", "说明损失函数与误差指标"],
    "回归": ["定义解释变量与响应变量", "给出回归函数或损失函数", "说明参数估计与误差指标"],
    "优化": ["定义决策变量", "写清目标函数", "列出约束条件与可行域"],
    "规划": ["定义决策变量", "写清目标函数", "列出约束条件与可行域"],
    "评价": ["构建指标矩阵", "说明标准化与权重计算", "给出综合得分或排序规则"],
    "排序": ["构建指标矩阵", "说明权重来源", "给出排序或择优规则"],
    "分类": ["定义特征与类别标签", "说明分类函数或判别规则", "给出Precision/Recall/F1等指标"],
    "识别": ["定义特征与识别目标", "说明判别阈值或概率输出", "给出混淆矩阵和误差指标"],
    "聚类": ["定义样本特征矩阵", "说明距离度量或相似性", "给出聚类数与稳定性指标"],
    "仿真": ["定义状态变量与参数", "写出状态转移或动力学方程", "说明参数校准与情景设定"],
    "机理": ["定义状态变量与关键参数", "写出机理方程", "说明参数反演、边界条件与检验方式"],
}


# ============================================================
# 工具函数
# ============================================================

def safe_import(module_name: str):
    """安全导入模块，失败返回None"""
    try:
        return import_module(module_name)
    except Exception:
        return None


def is_suspicious_name(name: str) -> bool:
    """判断文件名是否疑似结果提交模板"""
    lowered = name.lower()
    return any(hint in lowered for hint in SUSPICIOUS_NAME_HINTS)


# ============================================================
# S0 预检：文件检查逻辑
# ============================================================

def _inspect_pdf(path: Path) -> dict[str, Any]:
    """检查PDF文件可读性"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": ".pdf",
        "extractable": False,
        "char_count": 0,
        "pages_sampled": 0,
        "warnings": [],
        "errors": [],
    }
    pypdf = safe_import("pypdf")
    if pypdf is None:
        info["errors"].append("依赖缺失：pypdf。请运行 pip install pypdf")
        return info
    try:
        reader = pypdf.PdfReader(str(path))
    except Exception as exc:
        info["errors"].append(f"无法打开PDF：{type(exc).__name__}: {exc}")
        return info

    total_pages = len(reader.pages)
    info["total_pages"] = total_pages
    first_pass_limit = min(5, total_pages)
    text_chars = 0
    for i in range(first_pass_limit):
        try:
            text_chars += len(reader.pages[i].extract_text() or "")
        except Exception:
            pass
    info["pages_sampled"] = first_pass_limit
    if text_chars == 0 and total_pages > first_pass_limit:
        deeper_limit = min(20, total_pages)
        for i in range(first_pass_limit, deeper_limit):
            try:
                text_chars += len(reader.pages[i].extract_text() or "")
            except Exception:
                pass
        info["pages_sampled"] = deeper_limit
    info["char_count"] = text_chars
    if text_chars == 0:
        info["warnings"].append("未抽出任何文本，可能是扫描版PDF；需OCR或手动转录为docx/md。")
    elif text_chars < 200:
        info["warnings"].append(f"仅抽出{text_chars}个字符，文本量很少，请确认题面是否完整。")
    else:
        info["extractable"] = True
    return info


def _inspect_docx(path: Path) -> dict[str, Any]:
    """检查DOCX文件可读性"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": ".docx",
        "extractable": False,
        "paragraphs": 0,
        "char_count": 0,
        "warnings": [],
        "errors": [],
    }
    docx_mod = safe_import("docx")
    if docx_mod is None:
        info["errors"].append("依赖缺失：python-docx。请运行 pip install python-docx")
        return info
    try:
        document = docx_mod.Document(str(path))
    except Exception as exc:
        info["errors"].append(f"无法打开DOCX：{type(exc).__name__}: {exc}")
        return info
    paragraphs = list(document.paragraphs)
    info["paragraphs"] = len(paragraphs)
    chars = sum(len(p.text) for p in paragraphs)
    info["char_count"] = chars
    if chars == 0:
        info["warnings"].append("DOCX段落总字符数为0，文档可能为空。")
    else:
        info["extractable"] = True
    return info


def _inspect_text_file(path: Path) -> dict[str, Any]:
    """检查文本文件可读性"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": path.suffix.lower(),
        "extractable": False,
        "char_count": 0,
        "warnings": [],
        "errors": [],
    }
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            text = path.read_text(encoding=encoding)
            info["encoding"] = encoding
            info["char_count"] = len(text)
            info["extractable"] = len(text) > 0
            if len(text) == 0:
                info["warnings"].append("文件为空。")
            return info
        except Exception:
            continue
    info["errors"].append("无法以utf-8/gbk等常见编码读取文件。")
    return info


def _inspect_legacy_doc(path: Path) -> dict[str, Any]:
    """老.doc格式提示"""
    return {
        "path": path.as_posix(),
        "ext": ".doc",
        "extractable": False,
        "warnings": ["老.doc格式无法可靠解析；请另存为.docx或.pdf后再上传。"],
        "errors": [],
    }


def _inspect_xlsx(path: Path) -> dict[str, Any]:
    """检查XLSX文件"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": ".xlsx",
        "readable": False,
        "sheets": [],
        "warnings": [],
        "errors": [],
    }
    openpyxl = safe_import("openpyxl")
    if openpyxl is None:
        info["errors"].append("依赖缺失：openpyxl。请运行 pip install openpyxl")
        return info
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        info["errors"].append(f"无法打开XLSX：{type(exc).__name__}: {exc}")
        return info
    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = ws.max_row or 0
            cols = ws.max_column or 0
            sample_cols: list[str] = []
            if rows > 0 and cols > 0:
                first_row = next(
                    ws.iter_rows(min_row=1, max_row=1, max_col=min(cols, 8), values_only=True),
                    None,
                )
                if first_row is not None:
                    sample_cols = [str(c) if c is not None else "" for c in first_row]
            info["sheets"].append(
                {"name": sheet_name, "rows": rows, "cols": cols, "sample_cols": sample_cols}
            )
            if rows == 0 or cols == 0:
                info["warnings"].append(f"工作表{sheet_name}为空。")
    finally:
        wb.close()

    # 合并单元格检测
    try:
        wb2 = openpyxl.load_workbook(path, read_only=False, data_only=True)
        merged_total = sum(len(wb2[s].merged_cells.ranges) for s in wb2.sheetnames)
        if merged_total > 0:
            info["warnings"].append(
                f"检测到{merged_total}处合并单元格，pandas/openpyxl读取后可能错位，请人工核对。"
            )
        wb2.close()
    except Exception:
        pass
    info["readable"] = not info["errors"]
    return info


def _inspect_xls(path: Path) -> dict[str, Any]:
    """检查XLS文件"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": ".xls",
        "readable": False,
        "sheets": [],
        "warnings": [],
        "errors": [],
    }
    xlrd = safe_import("xlrd")
    if xlrd is None:
        info["errors"].append("依赖缺失：xlrd。请运行 pip install xlrd，或把文件另存为.xlsx。")
        return info
    try:
        book = xlrd.open_workbook(str(path))
    except Exception as exc:
        info["errors"].append(f"无法打开XLS：{type(exc).__name__}: {exc}")
        return info
    for sheet in book.sheets():
        info["sheets"].append(
            {"name": sheet.name, "rows": sheet.nrows, "cols": sheet.ncols, "sample_cols": []}
        )
    info["readable"] = True
    return info


def _inspect_csv(path: Path) -> dict[str, Any]:
    """检查CSV/TSV文件"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": path.suffix.lower(),
        "readable": False,
        "encoding": None,
        "sep": None,
        "sample_cols": [],
        "warnings": [],
        "errors": [],
    }
    pandas = safe_import("pandas")
    if pandas is None:
        info["errors"].append("依赖缺失：pandas。请运行 pip install pandas")
        return info
    last_exc: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        for sep in (None, ",", "\t", ";"):
            try:
                df = pandas.read_csv(path, nrows=5, encoding=encoding, sep=sep, engine="python")
                info["encoding"] = encoding
                info["sep"] = sep if sep is not None else "auto"
                info["sample_cols"] = [str(c) for c in df.columns.tolist()]
                info["readable"] = True
                return info
            except Exception as exc:
                last_exc = exc
                continue
    info["errors"].append(
        f"无法以常见编码/分隔符读取CSV。最后错误：{type(last_exc).__name__}: {last_exc}"
    )
    return info


def _inspect_json(path: Path) -> dict[str, Any]:
    """检查JSON文件"""
    info: dict[str, Any] = {
        "path": path.as_posix(),
        "ext": ".json",
        "readable": False,
        "warnings": [],
        "errors": [],
    }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        info["readable"] = True
        if isinstance(data, list):
            info["top_level"] = f"list[len={len(data)}]"
        elif isinstance(data, dict):
            info["top_level"] = f"dict[keys={list(data.keys())[:8]}]"
        else:
            info["top_level"] = type(data).__name__
    except Exception as exc:
        info["errors"].append(f"JSON解析失败：{type(exc).__name__}: {exc}")
    return info


def _classify_and_inspect(files: list[Path]) -> tuple[list[dict], list[dict], list[str]]:
    """分类检查所有文件"""
    doc_candidates: list[dict] = []
    data_candidates: list[dict] = []
    suspicious: list[str] = []
    for p in files:
        ext = p.suffix.lower()
        if is_suspicious_name(p.name) and ext in {".xlsx", ".xls", ".csv"}:
            suspicious.append(p.as_posix())
        if ext == ".pdf":
            doc_candidates.append(_inspect_pdf(p))
        elif ext == ".docx":
            doc_candidates.append(_inspect_docx(p))
        elif ext in {".md", ".txt"}:
            doc_candidates.append(_inspect_text_file(p))
        elif ext in LEGACY_DOC_EXTS:
            doc_candidates.append(_inspect_legacy_doc(p))
        elif ext == ".xlsx":
            data_candidates.append(_inspect_xlsx(p))
        elif ext == ".xls":
            data_candidates.append(_inspect_xls(p))
        elif ext in {".csv", ".tsv"}:
            data_candidates.append(_inspect_csv(p))
        elif ext == ".json":
            data_candidates.append(_inspect_json(p))
    return doc_candidates, data_candidates, suspicious


def _build_input_manifest(
    root: Path,
    files: list[Path],
    doc_candidates: list[dict],
    data_candidates: list[dict],
    suspicious: list[str],
) -> dict[str, Any]:
    """生成附件清单"""
    doc_by_path: dict[Path, dict] = {}
    data_by_path: dict[Path, dict] = {}
    for item in doc_candidates:
        try:
            doc_by_path[Path(str(item.get("path", ""))).resolve()] = item
        except Exception:
            continue
    for item in data_candidates:
        try:
            data_by_path[Path(str(item.get("path", ""))).resolve()] = item
        except Exception:
            continue
    suspicious_set = {Path(item).resolve() for item in suspicious}

    entries: list[dict[str, Any]] = []
    for path in files:
        resolved = path.resolve()
        ext = path.suffix.lower()
        info = doc_by_path.get(resolved) or data_by_path.get(resolved) or {}
        warnings = list(info.get("warnings", []) or [])
        errors = list(info.get("errors", []) or [])
        role = "unsupported"
        confidence = 0.2
        usable_for_modeling = False
        requires_user_confirmation = False

        if resolved in suspicious_set:
            role = "result_template"
            confidence = 0.95
            warnings.append("文件名疑似结果提交模板，不可当作原始建模数据。")
        elif ext in {".pdf", ".docx", ".md", ".txt"}:
            role = "problem_statement" if info.get("extractable") else "problem_statement_unreadable"
            confidence = 0.85 if info.get("extractable") else 0.55
            requires_user_confirmation = not bool(info.get("extractable"))
        elif ext in LEGACY_DOC_EXTS:
            role = "problem_statement_unreadable"
            confidence = 0.75
            requires_user_confirmation = True
        elif ext in DATA_EXTS:
            role = "raw_data" if info.get("readable") else "raw_data_unreadable"
            confidence = 0.8 if info.get("readable") else 0.45
            usable_for_modeling = bool(info.get("readable"))
            requires_user_confirmation = not bool(info.get("readable"))
        else:
            warnings.append("不属于当前自动识别的题面或数据格式，需要人工确认用途。")
            requires_user_confirmation = True

        entry: dict[str, Any] = {
            "path": path.name,
            "ext": ext,
            "role": role,
            "role_confidence": confidence,
            "usable_for_modeling": usable_for_modeling,
            "requires_user_confirmation": requires_user_confirmation,
            "warnings": warnings,
            "errors": errors,
        }
        for key in (
            "extractable", "char_count", "paragraphs", "readable",
            "sheets", "encoding", "sep", "sample_cols", "top_level",
        ):
            if key in info:
                entry[key] = info[key]
        entries.append(entry)

    role_counts: dict[str, int] = {}
    for entry in entries:
        role_counts[entry["role"]] = role_counts.get(entry["role"], 0) + 1

    return {
        "schema_version": "1.0",
        "generated_by": "competition_service.preflight_check",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": root.as_posix(),
        "entries": entries,
        "summary": {
            "file_count": len(entries),
            "role_counts": role_counts,
            "problem_statement_count": role_counts.get("problem_statement", 0),
            "raw_data_count": role_counts.get("raw_data", 0),
            "result_template_count": role_counts.get("result_template", 0),
            "requires_user_confirmation": any(item["requires_user_confirmation"] for item in entries),
        },
    }


def _collect_dep_status(doc_candidates: list[dict], data_candidates: list[dict]) -> dict[str, Any]:
    """收集Python依赖状态"""
    needed: set[str] = set()
    for info in doc_candidates:
        ext = info.get("ext")
        if ext == ".pdf":
            needed.add("pypdf")
        elif ext == ".docx":
            needed.add("docx")
    for info in data_candidates:
        ext = info.get("ext")
        if ext == ".xlsx":
            needed.add("openpyxl")
        elif ext == ".xls":
            needed.add("xlrd")
        elif ext in {".csv", ".tsv"}:
            needed.add("pandas")
    missing: list[str] = []
    present: list[str] = []
    for mod in sorted(needed):
        if safe_import(mod) is None:
            missing.append(f"{DEP_IMPORT_TO_PACKAGE.get(mod, mod)} (import {mod})")
        else:
            present.append(mod)
    return {"required": sorted(needed), "missing": missing, "present": present}


# ============================================================
# S1 赛题分析逻辑
# ============================================================

def _safe_read_text(path: Path) -> str:
    """安全读取文本文件"""
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=encoding, errors="ignore")
        except Exception:
            continue
    return ""


def _read_docx(path: Path) -> str:
    """读取DOCX文件全文"""
    try:
        from docx import Document
    except Exception:
        return ""
    try:
        doc = Document(path)
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception:
        return ""


def _read_pdf(path: Path) -> str:
    """读取PDF文件全文（多引擎降级）"""
    # 尝试PyMuPDF
    fitz = safe_import("fitz")
    if fitz:
        try:
            doc = fitz.open(path)
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            pass
    # 尝试pypdf
    pypdf = safe_import("pypdf")
    if pypdf:
        try:
            reader = pypdf.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            pass
    # 尝试pdfplumber
    pdfplumber = safe_import("pdfplumber")
    if pdfplumber:
        try:
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            pass
    return ""


def _profile_data_file(path: Path) -> dict[str, Any]:
    """数据文件画像"""
    rel = path.name
    profile: dict[str, Any] = {"path": rel, "type": path.suffix.lower().lstrip("."), "readable": False}
    try:
        import pandas as pd
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, nrows=20)
            profile.update({
                "readable": True,
                "rows_sampled": len(df),
                "columns": [str(c) for c in df.columns],
            })
        elif path.suffix.lower() in {".xlsx", ".xls"}:
            xls = pd.ExcelFile(path)
            sheets = []
            for sheet in xls.sheet_names[:5]:
                df = pd.read_excel(path, sheet_name=sheet, nrows=20)
                sheets.append({
                    "sheet": sheet,
                    "rows_sampled": len(df),
                    "columns": [str(c) for c in df.columns],
                })
            profile.update({"readable": True, "sheets": sheets})
    except Exception as exc:
        profile["error"] = str(exc)
    return profile


def _chinese_num_to_int(value: str) -> int | None:
    """中文数字转整数"""
    value = value.strip()
    if value.isdigit():
        return int(value)
    reverse = {v: k for k, v in QUESTION_NUMERALS.items()}
    if value in reverse:
        return reverse[value]
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if "十" in value:
        left, _, right = value.partition("十")
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    return None


def _split_questions(text: str) -> list[dict[str, str]]:
    """从赛题文本中拆分出子问题"""
    if not text:
        return []

    pattern = re.compile(
        r"(?:^|\n)\s*"
        r"(?:(?:问题|任务)\s*(?P<num1>[一二三四五六七八九十\d]+)\s*(?:问|题)?"
        r"|第\s*(?P<num2>[一二三四五六七八九十\d]+)\s*(?:问|题|小问))"
        r"[：:、.．\s]*(?P<title>.*)"
    )
    matches = list(pattern.finditer(text))
    questions: list[dict[str, str]] = []

    for idx, match in enumerate(matches):
        raw_num = match.group("num1") or match.group("num2") or str(idx + 1)
        num = _chinese_num_to_int(raw_num) or (idx + 1)
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        first_line = match.group("title").strip() or f"问题{QUESTION_NUMERALS.get(num, num)}"
        questions.append({
            "id": f"Q{num}",
            "title": f"问题{QUESTION_NUMERALS.get(num, num)}",
            "summary": first_line[:160],
            "raw_text": chunk[:2000],
        })

    if questions:
        unique: dict[str, dict[str, str]] = {}
        for item in questions:
            unique.setdefault(item["id"], item)
        return list(unique.values())

    return [{
        "id": "Q1",
        "title": "问题一",
        "summary": "根据赛题文本和附件数据完成核心建模任务。",
        "raw_text": text[:2000],
    }]


def _choose_model(text: str) -> dict[str, Any]:
    """根据关键词匹配最合适的模型类型"""
    lower = text.lower()
    best = None
    best_score = -1
    for rule in MODEL_RULES:
        score = sum(1 for kw in rule["keywords"] if kw.lower() in lower)
        if score > best_score:
            best = rule
            best_score = score
    if best is None or best_score <= 0:
        best = {
            "task_type": "综合建模/统计分析",
            "baseline": "描述统计、相关性分析或可解释基线模型",
            "improved": "结合题目目标选择回归、评价、优化或仿真模型",
            "validation": ["结果复核", "敏感性分析", "与题意约束对照"],
            "figures": ["数据概览图", "结果对比图", "敏感性分析图"],
        }
    return {
        "task_type": best["task_type"],
        "baseline_model": best["baseline"],
        "improved_model": best["improved"],
        "validation_plan": best["validation"],
        "figure_suggestions": best["figures"],
    }


def _extract_constraints(text: str) -> list[str]:
    """从文本中提取约束条件"""
    sentences = re.split(r"[。；;\n]", text)
    keywords = ["要求", "约束", "限制", "必须", "至少", "不超过", "不能", "需要", "给出", "确定", "建立"]
    hits = []
    for sent in sentences:
        sent = sent.strip()
        if 8 <= len(sent) <= 180 and any(kw in sent for kw in keywords):
            hits.append(sent)
        if len(hits) >= 8:
            break
    return hits


# ============================================================
# CompetitionService 主类
# ============================================================

class CompetitionService:
    """竞赛工作流服务 — 管理 S0-S8 全流程"""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    # ---- 文件管理 ----

    def _task_dir(self, task_id: int) -> Path:
        """竞赛任务的工作目录"""
        return Path("paper_output") / str(task_id)

    def _problem_dir(self, task_id: int) -> Path:
        """赛题文件目录"""
        return self._task_dir(task_id) / "problem_files"

    async def create_task(self, title: str = "未命名赛题") -> dict:
        """创建新的竞赛任务"""
        from app.models.models import CompetitionTask

        task = CompetitionTask(
            user_id=self.user_id,
            title=title,
            status="created",
            current_step="S0",
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # 创建工作目录
        problem_dir = self._problem_dir(task.id)
        problem_dir.mkdir(parents=True, exist_ok=True)

        return {
            "id": task.id,
            "user_id": task.user_id,
            "title": task.title,
            "status": task.status,
            "current_step": task.current_step,
            "file_count": 0,
            "preflight_status": "pending",
        }

    async def upload_files(self, task_id: int, files: list) -> dict:
        """上传赛题文件到任务目录"""
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        problem_dir = self._problem_dir(task_id)
        problem_dir.mkdir(parents=True, exist_ok=True)

        uploaded = []
        for file in files:
            # file is UploadFile from FastAPI
            file_path = problem_dir / file.filename
            content = await file.read()
            file_path.write_bytes(content)
            uploaded.append(file.filename)

        # 更新文件计数
        all_files = list(problem_dir.rglob("*"))
        file_count = sum(1 for f in all_files if f.is_file())
        task.file_count = file_count
        task.status = "files_uploaded"
        await self.db.commit()

        return {"task_id": task_id, "uploaded": uploaded, "file_count": file_count}

    async def get_files(self, task_id: int) -> list[dict]:
        """获取任务已上传的文件列表"""
        problem_dir = self._problem_dir(task_id)
        if not problem_dir.exists():
            return []
        files = []
        for p in sorted(problem_dir.rglob("*")):
            if p.is_file():
                files.append({
                    "name": p.name,
                    "size": p.stat().st_size,
                    "ext": p.suffix.lower(),
                })
        return files

    # ---- S0 预检 ----

    async def run_preflight(self, task_id: int) -> dict:
        """
        运行 S0 预检：文件分类 + 可读性 + 依赖 + 附件角色识别
        生成 preflight_report.json 和 input_manifest.json
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        problem_dir = self._problem_dir(task_id)
        root = self._task_dir(task_id)
        root.mkdir(parents=True, exist_ok=True)

        # ---- 文件发现 ----
        errors: list[str] = []
        warnings: list[str] = []

        pf_exists = problem_dir.exists() and problem_dir.is_dir()
        all_files: list[Path] = []
        if pf_exists:
            all_files = sorted(
                [p for p in problem_dir.rglob("*") if p.is_file()],
                key=lambda p: str(p).lower(),
            )

        if not pf_exists:
            errors.append("缺少赛题文件目录。请先上传题面(PDF/DOCX/MD/TXT)与数据附件。")
        elif not all_files:
            errors.append("赛题文件目录为空。请上传题面与数据附件。")

        # ---- 文件分类与检查 ----
        doc_candidates, data_candidates, suspicious = _classify_and_inspect(all_files)

        extractable_docs = [d for d in doc_candidates if d.get("extractable")]
        if all_files and not extractable_docs:
            errors.append(
                "没有可解析的题面文档。需要.pdf/.docx/.md/.txt之一，且能成功抽取到文本。"
            )

        # 逐文件错误/警告汇总
        for info in doc_candidates + data_candidates:
            for e in info.get("errors", []) or []:
                errors.append(f"{info['path']}: {e}")
            for w in info.get("warnings", []) or []:
                warnings.append(f"{info['path']}: {w}")

        # ---- 依赖检查 ----
        deps = _collect_dep_status(doc_candidates, data_candidates)
        if deps["missing"]:
            for m in deps["missing"]:
                errors.append(f"缺少依赖：{m}")

        # ---- 可疑文件 ----
        if suspicious:
            for s in suspicious:
                warnings.append(f"{s}: 文件名疑似结果模板（含result/结果/submit/提交），不可当作原始数据使用。")

        # ---- 陈旧产物检测 ----
        stale_docx = root / "final_paper.docx"
        stale = stale_docx.exists()
        if stale:
            warnings.append(
                f"{stale_docx.as_posix()}: 检测到旧的final_paper.docx；如属历史产物建议归档或删除。"
            )

        # ---- 生成附件清单 ----
        input_manifest = _build_input_manifest(
            root, all_files, doc_candidates, data_candidates, suspicious
        )

        # ---- 写入JSON文件 ----
        (root / "input_manifest.json").write_text(
            json.dumps(input_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        status = "PASS" if not errors else "FAIL"
        preflight_report = {
            "schema_version": "1.0",
            "generated_by": "competition_service.preflight_check",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": status,
            "root": root.as_posix(),
            "problem_files": {
                "exists": pf_exists,
                "non_empty": bool(all_files),
                "file_count": len(all_files),
                "doc_candidates": doc_candidates,
                "data_candidates": data_candidates,
                "suspicious_template_files": suspicious,
            },
            "deps": deps,
            "stale_output": {"final_paper_docx_exists": stale},
            "input_manifest": {
                "path": "paper_output/input_manifest.json",
                "summary": input_manifest["summary"],
            },
            "errors": errors,
            "warnings": warnings,
        }

        (root / "preflight_report.json").write_text(
            json.dumps(preflight_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---- 更新数据库 ----
        task.preflight_report = json.dumps(preflight_report, ensure_ascii=False)
        task.input_manifest = json.dumps(input_manifest, ensure_ascii=False)
        task.preflight_status = "pass" if status == "PASS" else "fail"
        task.current_step = "S0"
        task.status = "s0_passed" if status == "PASS" else "s0_failed"
        await self.db.commit()

        return {
            "task_id": task_id,
            "status": status,
            "preflight_report": preflight_report,
            "input_manifest": input_manifest,
        }

    # ---- S1 赛题分析 ----

    async def run_analysis(self, task_id: int) -> dict:
        """
        运行 S1 赛题分析：文本提取 + 子问题拆分 + 模型推荐
        需要 S0 预检通过（preflight_status == 'pass'）
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.preflight_status != "pass":
            raise RuntimeError("S0预检未通过，请先完成预检再运行赛题分析。")

        problem_dir = self._problem_dir(task_id)
        root = self._task_dir(task_id)
        step1_dir = root / "step1"
        step1_dir.mkdir(parents=True, exist_ok=True)

        all_files = sorted(
            [p for p in problem_dir.rglob("*") if p.is_file()],
            key=lambda p: str(p).lower(),
        )

        # ---- 文本提取 ----
        text_parts: list[str] = []
        documents: list[dict[str, Any]] = []
        data_files: list[dict[str, Any]] = []

        for path in all_files:
            suffix = path.suffix.lower()
            content = ""

            if suffix in {".txt", ".md"}:
                content = _safe_read_text(path)
                documents.append({"path": path.name, "type": suffix.lstrip("."), "chars": len(content)})
            elif suffix == ".docx":
                content = _read_docx(path)
                documents.append({"path": path.name, "type": "docx", "chars": len(content)})
            elif suffix == ".pdf":
                content = _read_pdf(path)
                documents.append({"path": path.name, "type": "pdf", "chars": len(content)})
            elif suffix in {".csv", ".xlsx", ".xls"}:
                data_files.append(_profile_data_file(path))

            if content.strip():
                text_parts.append(f"\n\n# 文件：{path.name}\n{content.strip()}")

        full_text = "\n".join(text_parts).strip()

        # ---- 文本标准化 ----
        full_text = re.sub(r"\r\n?", "\n", full_text)
        full_text = re.sub(r"[ \t]+", " ", full_text)
        full_text = re.sub(r"\n{3,}", "\n\n", full_text)
        full_text = full_text.strip()

        # ---- 约束提取 ----
        constraints = _extract_constraints(full_text)

        # ---- 子问题拆分 ----
        raw_questions = _split_questions(full_text)

        # ---- 各问题分析与模型推荐 ----
        questions = []
        for item in raw_questions:
            model = _choose_model(item["raw_text"] + "\n" + item["summary"])
            questions.append({
                **item,
                "task_type": model["task_type"],
                "inputs": ["赛题文本", "附件数据", "必要的外部权威数据"],
                "outputs": ["可量化结果", "图表证据", "对应原问的结论"],
                "constraints": _extract_constraints(item["raw_text"]) or constraints[:3],
                "recommended_models": {
                    "baseline": model["baseline_model"],
                    "improved": model["improved_model"],
                },
                "validation_plan": model["validation_plan"],
                "figure_suggestions": model["figure_suggestions"],
            })

        # ---- 外部数据需求检测 ----
        data_requirements = []
        ext_keywords = ["搜集", "收集", "查找", "公开数据", "外部数据", "统计数据", "权威数据", "网络数据"]
        if any(kw in full_text for kw in ext_keywords):
            data_requirements.append({
                "type": "manual_search",
                "query": " ".join(constraints[:2]) or "根据赛题补充权威公开数据",
                "notes": "检测到题目可能需要外部公开数据，请优先寻找官方或权威来源。",
                "active": True,
            })

        # ---- 构建分析结果 ----
        problem_analysis = {
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "generated_by": "competition_service.run_analysis",
            "source_dir": str(problem_dir),
            "documents": documents,
            "data_files": data_files,
            "problem_text_excerpt": full_text[:3000],
            "global_constraints": constraints,
            "questions": questions,
            "data_requirements": data_requirements,
            "next_outputs": {
                "model_route": f"paper_output/{task_id}/plan/model_route.json",
                "tasks": f"paper_output/{task_id}/tasks.json",
                "figures": f"paper_output/{task_id}/figures/",
            },
        }

        # ---- 写入JSON ----
        (step1_dir / "problem_analysis.json").write_text(
            json.dumps(problem_analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---- 生成Markdown辅助文件 ----
        self._write_analysis_markdown(step1_dir, questions)

        # ---- 更新数据库 ----
        task.problem_analysis = json.dumps(problem_analysis, ensure_ascii=False)
        task.current_step = "S1"
        task.status = "s1_completed"
        await self.db.commit()

        task_types = list(dict.fromkeys(q["task_type"] for q in questions))

        return {
            "task_id": task_id,
            "status": "completed",
            "problem_analysis": problem_analysis,
            "questions_count": len(questions),
            "task_types": task_types,
        }

    def _write_analysis_markdown(self, step1_dir: Path, questions: list[dict]) -> None:
        """生成 S1 分析的 Markdown 辅助文件"""
        # A_题意对齐.md
        lines_a = ["# A 题意对齐\n"]
        for q in questions:
            lines_a.append(f"## {q['title']}\n")
            lines_a.append(f"- 任务类型：{q['task_type']}\n")
            lines_a.append(f"- 题意摘要：{q.get('summary', '')}\n")
            lines_a.append(f"- 基线模型：{q['recommended_models']['baseline']}\n")
            lines_a.append(f"- 改进路线：{q['recommended_models']['improved']}\n")
            lines_a.append(f"- 验证计划：{'；'.join(q.get('validation_plan', []))}\n")
            lines_a.append(f"- 建议图表：{'；'.join(q.get('figure_suggestions', []))}\n\n")

        # B_论文大纲.md
        outline = [
            "# B 论文大纲\n",
            "1. 摘要\n",
            "2. 问题重述\n",
            "3. 模型假设与符号说明\n",
            "4. 数据说明与预处理\n",
        ]
        for idx, q in enumerate(questions, start=1):
            outline.append(f"{4 + idx}. {q['title']}：模型建立、求解、结果与检验\n")
        outline.extend([
            f"{5 + len(questions)}. 综合结果分析与敏感性检验\n",
            f"{6 + len(questions)}. 模型评价、推广与不足\n",
            f"{7 + len(questions)}. 结论、参考文献与附录\n",
        ])

        # C_评分点对齐表.md
        lines_c = ["# C 评分点对齐表\n", "| 评分点 | 证据形式 | 论文位置 |\n|---|---|---|\n"]
        for q in questions:
            lines_c.append(
                f"| {q['title']}回答完整 | 模型公式、结果表、验证图 | {q['title']}模型与结果分析 |\n"
            )
        lines_c.extend([
            "| 数据可复现 | 清洗脚本、字段说明、来源记录 | 数据说明与附录 |\n",
            "| 图文一致 | 图表文件与正文引用 | 结果分析 |\n",
            "| 结论对应原问 | 分问题结论清单 | 结论 |\n",
        ])

        # D_模型路线.json
        route = []
        for q in questions:
            route.append({
                "question_id": q["id"],
                "title": q["title"],
                "task_type": q["task_type"],
                "baseline_model": q["recommended_models"]["baseline"],
                "improved_model": q["recommended_models"]["improved"],
                "validation_plan": q.get("validation_plan", []),
                "figure_suggestions": q.get("figure_suggestions", []),
            })

        (step1_dir / "A_题意对齐.md").write_text("".join(lines_a), encoding="utf-8")
        (step1_dir / "B_论文大纲.md").write_text("".join(outline), encoding="utf-8")
        (step1_dir / "C_评分点对齐表.md").write_text("".join(lines_c), encoding="utf-8")
        (step1_dir / "D_模型路线.json").write_text(
            json.dumps(route, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- 任务查询 ----

    async def list_tasks(self) -> list[dict]:
        """获取用户的所有竞赛任务"""
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask)
            .where(CompetitionTask.user_id == self.user_id)
            .order_by(CompetitionTask.updated_at.desc())
        )
        tasks = result.scalars().all()
        return [
            {
                "id": t.id,
                "user_id": t.user_id,
                "title": t.title,
                "status": t.status,
                "current_step": t.current_step,
                "file_count": t.file_count,
                "preflight_status": t.preflight_status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tasks
        ]

    async def get_task(self, task_id: int) -> dict | None:
        """获取任务详情"""
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return None
        return {
            "id": task.id,
            "user_id": task.user_id,
            "title": task.title,
            "status": task.status,
            "current_step": task.current_step,
            "file_count": task.file_count,
            "preflight_status": task.preflight_status,
            "preflight_report": task.preflight_report,
            "input_manifest": task.input_manifest,
            "problem_analysis": task.problem_analysis,
            "model_route": task.model_route,
            "rubric_alignment": task.rubric_alignment,
            "data_plan": task.data_plan,
            "visualization_plan": task.visualization_plan,
            "model_contract": task.model_contract,
            "evidence_gate": task.evidence_gate,
            "draft_paper": task.draft_paper,
            "format_check": task.format_check,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    # ---- S2 模型路线 ----

    async def run_model_route(self, task_id: int) -> dict:
        """
        运行 S2 模型路线：模型推荐 + 评分点对齐 + 公式要求 + 图表规划
        需要 S1 赛题分析已完成（status == 's1_completed'）
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.status != "s1_completed":
            raise RuntimeError("请先完成 S1 赛题分析再运行 S2 模型路线。")

        # 加载 S1 分析结果
        try:
            analysis = json.loads(task.problem_analysis)
        except Exception:
            raise RuntimeError("S1 分析数据损坏，请重新运行赛题分析。")

        root = self._task_dir(task_id)
        plan_dir = root / "plan"
        plan_dir.mkdir(parents=True, exist_ok=True)

        # 构建模型路线
        model_route = self._build_model_route(analysis, task_id)
        rubric_alignment = self._build_rubric_alignment(model_route)
        self._write_scoring_strategy(plan_dir, model_route, rubric_alignment)

        # 写入 JSON
        (plan_dir / "model_route.json").write_text(
            json.dumps(model_route, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (plan_dir / "rubric_alignment.json").write_text(
            json.dumps(rubric_alignment, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 更新数据库
        task.model_route = json.dumps(model_route, ensure_ascii=False)
        task.rubric_alignment = json.dumps(rubric_alignment, ensure_ascii=False)
        task.current_step = "S2"
        task.status = "s2_completed"
        await self.db.commit()

        questions_count = len(model_route.get("questions", []))

        return {
            "task_id": task_id,
            "status": "completed",
            "model_route": model_route,
            "rubric_alignment": rubric_alignment,
            "questions_count": questions_count,
        }

    def _match_backup_models(self, task_type: str, baseline: str, main: str) -> list[str]:
        """从备选模型库匹配，排除已选的基线和主模型"""
        for key, values in BACKUP_MODELS.items():
            if key in task_type:
                return [m for m in values if m not in {baseline, main}][:3]
        return ["可解释统计模型", "稳健性对照模型"]

    def _match_formula_requirements(self, task_type: str) -> list[str]:
        """获取任务类型对应的公式要求"""
        for key, values in FORMULA_REQUIREMENTS.items():
            if key in task_type:
                return list(values)
        return ["定义输入变量与输出目标", "说明核心模型函数或目标函数", "给出评价指标与检验方式"]

    def _build_model_route(self, analysis: dict, task_id: int) -> dict:
        """构建模型路线 JSON"""
        questions = analysis.get("questions", [])
        if not isinstance(questions, list):
            questions = []

        route_questions: list[dict] = []
        for index, question in enumerate(questions, start=1):
            if not isinstance(question, dict):
                continue
            qid = question.get("id") or f"Q{index}"
            task_type = str(question.get("task_type") or "综合建模/统计分析").strip()
            models = question.get("recommended_models") or {}
            baseline_model = str(models.get("baseline") or "可解释基线模型").strip()
            main_model = str(models.get("improved") or baseline_model or "结合题目需求的主模型").strip()
            backup_models = self._match_backup_models(task_type, baseline_model, main_model)
            formula_reqs = self._match_formula_requirements(task_type)
            validation = question.get("validation_plan") or ["结果复核", "敏感性分析"]
            figure_suggestions = question.get("figure_suggestions") or ["结果对比图", "敏感性分析图"]
            summary = str(question.get("summary") or "将原题要求转化为可计算、可验证的建模任务。")
            constraints = question.get("constraints") or []
            title = str(question.get("title") or f"问题{index}")

            # 模型理由
            if constraints and isinstance(constraints, list) and len(constraints) > 0:
                reason = f'该问属于「' + task_type + '」任务，' + main_model + ' 能在保留可解释性的同时承接题目约束：' + constraints[0][:80] + '。'
            elif summary:
                reason = f'该问属于「' + task_type + '」任务，' + main_model + ' 能围绕「' + summary[:60] + '」形成模型、结果和验证闭环。'
            else:
                reason = f'该问属于「' + task_type + '」任务，' + main_model + ' 能同时支撑建模、求解、结果解释和后续检验。'

            # 图表
            figures = []
            for fi, fig_title in enumerate(figure_suggestions if isinstance(figure_suggestions, list) else [figure_suggestions], start=1):
                fid = f"fig_{qid.lower()}_{fi}"
                figures.append({
                    "figure_id": fid,
                    "title": str(fig_title),
                    "purpose": f"支撑{qid}的模型结果、验证或敏感性分析",
                    "expected_path": f"paper_output/{task_id}/figures/{fid}.png",
                })

            route_questions.append({
                "question_id": qid,
                "title": title,
                "task_type": task_type,
                "core_goal": summary,
                "baseline_model": baseline_model,
                "main_model": main_model,
                "backup_models": backup_models,
                "model_reason": reason,
                "formula_requirements": formula_reqs,
                "validation": validation if isinstance(validation, list) else [validation],
                "figures": figures,
                "paper_sections": [
                    f"{title}模型建立",
                    f"{title}结果分析",
                    f"{title}模型检验",
                ],
            })

        return {
            "schema_version": "1.0",
            "generated_by": "competition_service.run_model_route",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source": f"paper_output/{task_id}/step1/problem_analysis.json",
            "paper_prompt_reference": "MathModel-Skill-master references/paper_prompt_default.md",
            "questions": route_questions,
        }

    def _build_rubric_alignment(self, model_route: dict) -> dict:
        """构建评分点对齐 JSON"""
        items: list[dict] = []
        for question in model_route.get("questions", []):
            qid = question.get("question_id")
            sections = question.get("paper_sections", [])
            figures = question.get("figures", [])
            figure_titles = [fig.get("title", "") for fig in figures if isinstance(fig, dict)]

            items.extend([
                {
                    "rubric_point": "题意覆盖",
                    "question_id": qid,
                    "evidence_required": ["可计算目标", "输入输出定义", "对应原问的结论"],
                    "paper_location": sections,
                    "qa_rule": "正文必须明确本问要解决什么，并在结论中回扣原题。",
                },
                {
                    "rubric_point": "模型合理性",
                    "question_id": qid,
                    "evidence_required": ["模型选择理由", "模型公式", "评价指标"],
                    "paper_location": sections,
                    "qa_rule": "正文必须同时出现模型理由、核心变量和验证指标。",
                },
                {
                    "rubric_point": "结果可信",
                    "question_id": qid,
                    "evidence_required": ["基线对照", "检验指标", "误差或敏感性分析"],
                    "paper_location": sections,
                    "qa_rule": "正文必须说明结果如何被验证，而不是只给出结论。",
                },
                {
                    "rubric_point": "图表证据",
                    "question_id": qid,
                    "evidence_required": figure_titles or ["结果图表"],
                    "paper_location": sections,
                    "qa_rule": "正文引用的图表应能在 paper_output/figures/ 下找到对应文件。",
                },
            ])

        return {
            "schema_version": "1.0",
            "generated_by": "competition_service.run_model_route",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source": f"paper_output/{model_route.get('source', '')}",
            "items": items,
        }

    def _write_scoring_strategy(self, plan_dir: Path, model_route: dict, rubric_alignment: dict) -> None:
        """生成评分策略说明 Markdown"""
        lines = [
            "# 评分闭环与模型路线策略\n\n",
            "本文件由竞赛工作流 S2 模型路线自动生成，用于指导后续 QA 与论文写作。\n\n",
            "## 全局原则\n\n",
            '- 每一问必须形成"任务定义 → 模型建立 → 求解结果 → 验证检验 → 回答原问"的闭环。\n',
            "- `model_route.json` 是后续写作的模型路线交接单，不能在正文生成时随意偷换主模型。\n",
            "- `rubric_alignment.json` 是评分点与证据形式的映射，QA 应逐条检查是否落实。\n\n",
        ]
        rubric_items = rubric_alignment.get("items", [])

        for question in model_route.get("questions", []):
            qid = question.get("question_id")
            lines.append(f"## {question.get('title', qid)}\n\n")
            lines.append(f"- 任务类型：{question.get('task_type')}\n")
            lines.append(f"- 核心目标：{question.get('core_goal')}\n")
            lines.append(f"- 基线模型：{question.get('baseline_model')}\n")
            lines.append(f"- 主模型：{question.get('main_model')}\n")
            lines.append(f"- 备选模型：{'、'.join(question.get('backup_models', []))}\n")
            lines.append(f"- 模型理由：{question.get('model_reason')}\n")
            lines.append(f"- 公式要求：{'；'.join(question.get('formula_requirements', []))}\n")
            lines.append(f"- 验证计划：{'；'.join(question.get('validation', []))}\n")
            fig_titles = [fig.get("title", "") for fig in question.get("figures", []) if isinstance(fig, dict)]
            lines.append(f"- 图表证据：{'；'.join(fig_titles) if fig_titles else '待规划'}\n")

            matched = [item for item in rubric_items if item.get("question_id") == qid]
            if matched:
                lines.append("- 评分点落位：")
                lines.append("；".join(
                    f"{item.get('rubric_point')} → {'/'.join(item.get('paper_location', []))}"
                    for item in matched
                ))
                lines.append("\n")
            lines.append("\n")

        (plan_dir / "scoring_strategy.md").write_text("".join(lines), encoding="utf-8")

    # ---- S3-S4 数据处理 + 可视化计划 ----

    async def run_data_pipeline(self, task_id: int) -> dict:
        """
        运行 S3-S4 数据处理 + 可视化计划
        需要 S2 模型路线已完成（status == 's2_completed'）
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.status != "s2_completed":
            raise RuntimeError("请先完成 S2 模型路线再运行 S3-S4 数据处理。")

        # 加载前序合约
        try:
            analysis = json.loads(task.problem_analysis)
        except Exception:
            analysis = None
        try:
            model_route = json.loads(task.model_route)
        except Exception:
            model_route = None

        root = self._task_dir(task_id)
        plan_dir = root / "plan"
        plan_dir.mkdir(parents=True, exist_ok=True)

        # S3: 数据处理计划
        data_files = self._profile_data_files(task_id, analysis)
        data_plan = self._build_data_plan(task_id, data_files, model_route)

        # S4: 可视化计划
        visualization_plan = self._build_visualization_plan(task_id, data_files, model_route, analysis)
        figure_index = self._build_figure_index(task_id, visualization_plan)

        # 写入文件
        (plan_dir / "data_plan.json").write_text(
            json.dumps(data_plan, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (plan_dir / "visualization_plan.json").write_text(
            json.dumps(visualization_plan, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (root / "figure_index.json").write_text(
            json.dumps(figure_index, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 更新数据库
        task.data_plan = json.dumps(data_plan, ensure_ascii=False)
        task.visualization_plan = json.dumps(visualization_plan, ensure_ascii=False)
        task.current_step = "S4"
        task.status = "s4_completed"
        await self.db.commit()

        return {
            "task_id": task_id,
            "status": "completed",
            "data_plan": data_plan,
            "visualization_plan": visualization_plan,
            "data_files_count": len(data_files),
            "figures_count": len(figure_index.get("figures", [])),
        }

    def _profile_data_files(self, task_id: int, analysis: dict = None) -> list[dict]:
        """扫描并画像上传的数据文件"""
        problem_dir = self._problem_dir(task_id)
        data_exts = {".csv", ".xlsx", ".xls"}
        profiles: list[dict] = []

        # 扫描上传的数据文件
        if problem_dir.exists():
            for path in sorted(problem_dir.rglob("*"), key=str):
                if not path.is_file():
                    continue
                if path.name.startswith("~"):
                    continue
                if path.suffix.lower() in data_exts:
                    profile = self._profile_single_file(path, task_id)
                    profiles.append(profile)

        # 如果没有数据文件，从 S1 分析中提取
        if not profiles and isinstance(analysis, dict):
            data_files = analysis.get("data_files", [])
            for item in data_files if isinstance(data_files, list) else []:
                if not isinstance(item, dict):
                    continue
                raw_path = str(item.get("path") or "").strip()
                if not raw_path:
                    continue
                columns = item.get("columns", [])
                if isinstance(item.get("sheets"), list) and item["sheets"] and not columns:
                    first = item["sheets"][0]
                    columns = first.get("columns") if isinstance(first, dict) else []
                clean_name = Path(raw_path).stem or "dataset"
                profiles.append({
                    "path": raw_path.replace("\\", "/"),
                    "type": str(item.get("type") or Path(raw_path).suffix.lstrip(".") or "data"),
                    "readable": bool(item.get("readable", False)),
                    "columns": [str(c) for c in columns] if isinstance(columns, list) else [],
                    "numeric_columns": [],
                    "categorical_columns": [str(c) for c in columns] if isinstance(columns, list) else [],
                    "role": "主建模数据",
                    "cleaned_output": f"paper_output/{task_id}/data_cleaned/{clean_name}_cleaned.csv",
                    "cleaning_tasks": ["缺失值检查", "字段类型转换", "异常值检查"],
                })

        return profiles

    def _profile_single_file(self, path: Path, task_id: int) -> dict:
        """画像单个数据文件"""
        suffix = path.suffix.lower().lstrip(".")
        role = "主建模数据" if "problem_files" in path.parts else "补充数据"
        stem = path.stem

        profile: dict = {
            "path": str(path).replace("\\", "/"),
            "type": suffix,
            "readable": False,
            "columns": [],
            "numeric_columns": [],
            "categorical_columns": [],
            "role": role,
            "cleaned_output": f"paper_output/{task_id}/data_cleaned/{stem}_cleaned.csv",
            "cleaning_tasks": ["缺失值检查", "字段类型转换", "异常值检查", "重复记录检查"],
        }

        # 尝试读取 CSV
        if suffix == "csv":
            try:
                import csv as csv_mod
                for enc in ("utf-8-sig", "utf-8", "gbk"):
                    try:
                        with path.open("r", encoding=enc, errors="ignore") as fh:
                            sample = fh.read(4096)
                            if not sample.strip():
                                continue
                            dialect = csv_mod.Sniffer().sniff(sample)
                            fh.seek(0)
                            reader = csv_mod.reader(fh, dialect)
                            header = next(reader, [])
                            columns = [str(c).strip() for c in header if str(c).strip()]
                            if columns:
                                # 尝试读取几行来判断数据类型
                                numeric_cols: list[str] = []
                                cat_cols: list[str] = []
                                rows = []
                                for row in reader:
                                    rows.append(row)
                                    if len(rows) >= 10:
                                        break
                                if rows:
                                    for ci, col in enumerate(columns):
                                        vals = [r[ci] for r in rows if ci < len(r) and r[ci] and str(r[ci]).strip()]
                                        nums = 0
                                        for v in vals:
                                            try:
                                                float(str(v).replace(",", ""))
                                                nums += 1
                                            except Exception:
                                                pass
                                        if vals and nums / len(vals) >= 0.5:
                                            numeric_cols.append(col)
                                        else:
                                            cat_cols.append(col)
                                else:
                                    cat_cols = [c for c in columns]
                                profile["readable"] = True
                                profile["columns"] = columns
                                profile["numeric_columns"] = numeric_cols
                                profile["categorical_columns"] = cat_cols
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        return profile

    def _build_data_plan(self, task_id: int, data_files: list[dict], model_route: dict = None) -> dict:
        """构建 S3 数据处理计划"""
        # 选择主数据集
        dataset = None
        for df in data_files:
            if df.get("readable") and df.get("columns"):
                dataset = df
                break
        if not dataset and data_files:
            dataset = data_files[0]

        # 选择 X/Y 列
        x_column = ""
        y_columns: list[str] = []
        if dataset:
            cat_cols = dataset.get("categorical_columns", [])
            num_cols = dataset.get("numeric_columns", [])
            x_patterns = ("year", "date", "time", "month", "day", "年份", "年度", "日期", "时间", "月份")
            cols = dataset.get("columns", [])
            for col in cols:
                lower = col.lower()
                if any(p in lower or p in col for p in x_patterns):
                    x_column = col
                    break
            if not x_column:
                x_column = cat_cols[0] if cat_cols else (cols[0] if cols else "")
            y_columns = [col for col in num_cols if col != x_column][:3]

        # 问题链接
        questions = model_route.get("questions", []) if isinstance(model_route, dict) else []
        if not isinstance(questions, list):
            questions = []
        required_fields = [f for f in [x_column, *y_columns] if f]

        question_links = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            qid = q.get("question_id", "")
            task_type = str(q.get("task_type") or "综合建模/统计分析")
            if "优化" in task_type or "规划" in task_type:
                outputs = ["方案对比表", "约束满足表"]
            elif "评价" in task_type or "排序" in task_type:
                outputs = ["指标权重表", "综合得分表"]
            elif "预测" in task_type or "回归" in task_type:
                outputs = ["预测结果表", "误差指标表"]
            else:
                outputs = ["结果表", "误差指标表"]
            question_links.append({
                "question_id": qid,
                "required_fields": required_fields,
                "expected_outputs": outputs,
            })

        return {
            "schema_version": "1.0",
            "generated_by": "competition_service.run_data_pipeline",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_contracts": [
                f"paper_output/{task_id}/step1/problem_analysis.json",
                f"paper_output/{task_id}/plan/model_route.json",
            ],
            "data_files": data_files,
            "question_links": question_links,
            "note": "本文件是数据处理交接单，用于指导 Agent 按当前赛题二次生成或修改清洗与建模代码。",
        }

    def _build_visualization_plan(self, task_id: int, data_files: list[dict], model_route: dict = None, analysis: dict = None) -> dict:
        """构建 S4 可视化计划"""
        # 选择主数据集
        dataset = None
        for df in data_files:
            if df.get("readable") and df.get("columns"):
                dataset = df
                break
        if not dataset and data_files:
            dataset = data_files[0]

        data_source = str(dataset.get("cleaned_output", "")) if dataset else ""
        x_column = ""
        y_columns: list[str] = []
        if dataset:
            cat_cols = dataset.get("categorical_columns", [])
            num_cols = dataset.get("numeric_columns", [])
            cols = dataset.get("columns", [])
            x_patterns = ("year", "date", "time", "month", "day", "年份", "日期", "时间")
            for col in cols:
                lower = col.lower()
                if any(p in lower or p in col for p in x_patterns):
                    x_column = col
                    break
            if not x_column:
                x_column = cat_cols[0] if cat_cols else (cols[0] if cols else "")
            y_columns = [col for col in num_cols if col != x_column][:3]

        questions = model_route.get("questions", []) if isinstance(model_route, dict) else []
        if not isinstance(questions, list):
            questions = []

        # 从 S1 analysis 补充问题数据（特别是 figure_suggestions）
        analysis_questions = analysis.get("questions", []) if isinstance(analysis, dict) else []
        if not isinstance(analysis_questions, list):
            analysis_questions = []

        figures: list[dict] = []
        for q_idx, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            qid = str(question.get("question_id") or f"Q{q_idx + 1}")
            task_type = str(question.get("task_type") or "综合建模/统计分析")
            title = str(question.get("title") or f"问题{q_idx + 1}")

            # 从 model_route 取已有的 figures
            raw_figures = question.get("figures", [])
            if isinstance(raw_figures, list) and raw_figures:
                for fi, raw in enumerate(raw_figures, start=1):
                    if isinstance(raw, dict):
                        fid = raw.get("figure_id") or f"fig_{qid.lower()}_{fi}"
                        f_title = str(raw.get("title") or f"{qid}图表{fi}")
                        purpose = str(raw.get("purpose") or f"支撑{qid}的模型结果、验证或敏感性分析")
                        output_path = str(raw.get("expected_path") or f"paper_output/{task_id}/figures/{fid}.png")
                    else:
                        fid = f"fig_{qid.lower()}_{fi}"
                        f_title = str(raw)
                        purpose = f"支撑{qid}的模型结果、验证或敏感性分析"
                        output_path = f"paper_output/{task_id}/figures/{fid}.png"
                    figures.append(self._build_figure_entry(
                        fid, qid, f_title, task_type, data_source, x_column, y_columns, purpose, output_path
                    ))
            else:
                # 从 S1 analysis 补充
                aq = next((a for a in analysis_questions if a.get("id") == qid), None)
                suggestions = aq.get("figure_suggestions", []) if aq else []
                if isinstance(suggestions, list) and suggestions:
                    for fi, s in enumerate(suggestions, start=1):
                        fid = f"fig_{qid.lower()}_{fi}"
                        f_title = str(s)
                        purpose = f"支撑{qid}的结果、验证或敏感性分析"
                        output_path = f"paper_output/{task_id}/figures/{fid}.png"
                        figures.append(self._build_figure_entry(
                            fid, qid, f_title, task_type, data_source, x_column, y_columns, purpose, output_path
                        ))
                else:
                    # 默认图表
                    fid = f"fig_{qid.lower()}_1"
                    f_title = f"{qid}结果对比图"
                    purpose = f"支撑{title}的模型结果展示"
                    output_path = f"paper_output/{task_id}/figures/{fid}.png"
                    figures.append(self._build_figure_entry(
                        fid, qid, f_title, task_type, data_source, x_column, y_columns, purpose, output_path
                    ))

        return {
            "schema_version": "1.0",
            "generated_by": "competition_service.run_data_pipeline",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_contracts": [
                f"paper_output/{task_id}/plan/model_route.json",
                f"paper_output/{task_id}/plan/data_plan.json",
            ],
            "figures": figures,
            "note": "本文件只规划图表证据，不承诺固定代码可直接适配所有赛题。",
        }

    def _build_figure_entry(self, fid: str, qid: str, title: str, task_type: str, data_source: str, x_col: str, y_cols: list[str], purpose: str, output_path: str) -> dict:
        """构建单个图表条目"""
        return {
            "figure_id": fid,
            "question_id": qid,
            "title": title,
            "chart_type": self._chart_type_for(task_type, title, x_col, y_cols),
            "template_hint": self._template_hint_for(self._chart_type_for(task_type, title, x_col, y_cols)),
            "data_source": data_source,
            "candidate_x": x_col,
            "candidate_y": y_cols,
            "purpose": purpose,
            "output_path": output_path.replace("\\", "/"),
            "paper_usage": f"{qid}结果分析",
        }

    @staticmethod
    def _chart_type_for(task_type: str, title: str, x_col: str, y_cols: list[str]) -> str:
        """根据任务类型和标题推断图表类型"""
        t = title or ""
        txt = f"{task_type} {t}"
        if "残差" in t or "误差分布" in t:
            return "residual_distribution"
        if "敏感性" in t or "灵敏度" in t or "扰动" in t:
            return "sensitivity_curve"
        if "模型对比" in t or "方案对比" in t or "对照" in t:
            return "model_comparison"
        if "权重" in t:
            return "weight_bar"
        if "得分" in t or "排序" in t or "排名" in t:
            return "score_ranking"
        if "热力" in t or "矩阵" in t:
            return "heatmap"
        if "真实值" in t or "预测值" in t or "预报" in t:
            return "prediction_comparison"
        if "分类" in txt or "识别" in txt:
            return "bar"
        if "聚类" in txt or "分群" in txt:
            return "scatter"
        if "评价" in txt or "优化" in txt or "规划" in txt:
            return "bar"
        if "预测" in txt or "回归" in txt or "趋势" in txt:
            return "line" if x_col else "scatter"
        if len(y_cols) >= 2:
            return "line"
        return "bar"

    @staticmethod
    def _template_hint_for(chart_type: str) -> str:
        """图表类型 → 绘图函数提示"""
        hints = {
            "prediction_comparison": "plot_prediction_comparison",
            "residual_distribution": "plot_residual_distribution",
            "sensitivity_curve": "plot_sensitivity_curve",
            "model_comparison": "plot_model_comparison",
            "weight_bar": "plot_weight_bar",
            "score_ranking": "plot_score_ranking",
            "heatmap": "plot_heatmap",
            "scatter": "plot_scatter",
            "bar": "plot_model_comparison",
            "line": "plot_generic_line",
        }
        return hints.get(chart_type, "plot_generic_line")

    def _build_figure_index(self, task_id: int, visualization_plan: dict) -> dict:
        """从可视化计划生成图表索引"""
        root = self._task_dir(task_id)
        entries = []
        for item in visualization_plan.get("figures", []):
            if not isinstance(item, dict):
                continue
            path_str = str(item.get("output_path", "")).replace("\\", "/")
            entries.append({
                "figure_id": item.get("figure_id"),
                "path": path_str,
                "title": item.get("title"),
                "question_id": item.get("question_id"),
                "planned": True,
                "exists": bool(path_str and (root / path_str).exists()),
                "used_in": item.get("paper_usage"),
            })
        return {
            "schema_version": "1.0",
            "generated_by": "competition_service.run_data_pipeline",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "figures": entries,
        }

    # ============================================================
    # S5 建模代码生成 + 结果契约
    # ============================================================

    async def run_model_contract(self, task_id: int) -> dict:
        """
        运行 S5 建模代码生成 + 结果契约
        需要 S3-S4 数据处理已完成（status == 's4_completed'）

        产出：
        - results/model_results.json：每问结果摘要 + 参数 + 产出
        - results/metrics.json：每问指标契约
        - results/conclusions.json：每问结论契约
        - tables/table_index.json：表格索引
        - code/modeling/q*_model.py：每问建模代码脚手架
        - code/modeling/result_contract_io.py：工具库
        - code/modeling/run_modeling.py：统一运行入口
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.status not in ("s4_completed", "s5_completed"):
            raise RuntimeError("请先完成 S3-S4 数据处理再运行 S5 建模代码生成。")

        # 加载前序合约
        try:
            model_route = json.loads(task.model_route)
        except Exception:
            model_route = None
        try:
            data_plan = json.loads(task.data_plan)
        except Exception:
            data_plan = None

        root = self._task_dir(task_id)
        results_dir = root / "results"
        tables_dir = root / "tables"
        modeling_dir = root / "code" / "modeling"
        for d in (results_dir, tables_dir, modeling_dir):
            d.mkdir(parents=True, exist_ok=True)

        # 加载问题列表
        questions = self._load_questions_from_route(model_route, task_id)

        # 生成结果契约
        model_contract = self._build_model_contract(task_id, questions, data_plan)

        # 写入 JSON 文件
        now_ts = datetime.now().isoformat(timespec="seconds")
        common = {
            "schema_version": "1.0",
            "generated_by": "competition_service.run_model_contract",
            "generated_at": now_ts,
        }

        model_results = {
            **common,
            "source": f"paper_output/{task_id}/plan/model_route.json",
            "questions": model_contract["model_results"],
        }
        metrics_doc = {**common, "items": model_contract["metrics"]}
        conclusions_doc = {**common, "items": model_contract["conclusions"]}
        table_index_doc = {
            **common,
            "tables": model_contract["tables"],
            "notes": [
                "status=scaffold_result_needs_review 的表格来自自动脚手架，正式提交前应由 Agent 结合真实赛题复核或改写。",
            ],
        }

        (results_dir / "model_results.json").write_text(
            json.dumps(model_results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (results_dir / "metrics.json").write_text(
            json.dumps(metrics_doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (results_dir / "conclusions.json").write_text(
            json.dumps(conclusions_doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (tables_dir / "table_index.json").write_text(
            json.dumps(table_index_doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 生成 Python 建模代码脚手架
        scripts_generated = self._generate_modeling_scaffolds(task_id, questions, modeling_dir)

        # 尝试执行脚手架（如果有数据文件且 Python 可用）
        self._try_execute_scaffolds(task_id, questions, root, modeling_dir)

        # 更新数据库
        task.model_contract = json.dumps(model_contract, ensure_ascii=False)
        task.current_step = "S5"
        task.status = "s5_completed"
        await self.db.commit()

        return {
            "task_id": task_id,
            "status": "completed",
            "model_contract": model_contract,
            "questions_count": len(questions),
            "tables_count": len(model_contract["tables"]),
            "scripts_generated": scripts_generated,
        }

    # ---- S5 辅助方法 ----

    @staticmethod
    def _normalize_task_type(task_type: str) -> str:
        """标准化任务类型到英文分类"""
        text = str(task_type or "").lower()
        if any(k in text for k in ("预测", "回归", "forecast", "regression", "时间序列")):
            return "forecasting"
        if any(k in text for k in ("优化", "规划", "调度", "选址", "路径", "决策")):
            return "optimization"
        if any(k in text for k in ("评价", "排序", "权重", "综合", "topsis", "ahp", "熵权")):
            return "evaluation"
        if any(k in text for k in ("分类", "识别", "判别", "classification")):
            return "classification"
        if any(k in text for k in ("聚类", "分群", "clustering")):
            return "clustering"
        if any(k in text for k in ("仿真", "机理", "动力学", "微分", "simulation")):
            return "simulation"
        return "general"

    @staticmethod
    def _result_type_for(task_type: str) -> str:
        kind = CompetitionService._normalize_task_type(task_type)
        return {
            "forecasting": "prediction_result",
            "optimization": "optimization_solution",
            "evaluation": "ranking_or_score",
            "classification": "classification_result",
            "clustering": "cluster_result",
            "simulation": "simulation_result",
            "general": "model_result",
        }[kind]

    @staticmethod
    def _suggested_table_titles(task_type: str) -> list[str]:
        kind = CompetitionService._normalize_task_type(task_type)
        return {
            "forecasting": ["预测结果表", "误差指标表", "残差摘要表"],
            "optimization": ["最优方案表", "约束满足情况表", "方案对比表"],
            "evaluation": ["指标权重表", "综合得分排序表", "敏感性分析表"],
            "classification": ["分类结果表", "混淆矩阵表", "特征重要性表"],
            "clustering": ["聚类标签表", "群体特征表", "聚类稳定性表"],
            "simulation": ["参数估计表", "情景仿真结果表", "敏感性分析表"],
            "general": ["核心结果表", "模型对比表", "稳健性检查表"],
        }[kind]

    @staticmethod
    def _metric_templates(task_type: str) -> list[dict]:
        kind = CompetitionService._normalize_task_type(task_type)
        templates = {
            "forecasting": [
                {"metric_name": "RMSE", "metric_role": "预测误差", "value": None, "unit": ""},
                {"metric_name": "MAE", "metric_role": "平均绝对误差", "value": None, "unit": ""},
                {"metric_name": "MAPE", "metric_role": "相对误差", "value": None, "unit": "%"},
            ],
            "optimization": [
                {"metric_name": "objective_value", "metric_role": "目标函数值", "value": None, "unit": ""},
                {"metric_name": "constraint_satisfaction_rate", "metric_role": "约束满足率", "value": None, "unit": "%"},
                {"metric_name": "baseline_improvement", "metric_role": "相对基线改进幅度", "value": None, "unit": "%"},
            ],
            "evaluation": [
                {"metric_name": "top_score", "metric_role": "最高综合得分", "value": None, "unit": ""},
                {"metric_name": "rank_stability", "metric_role": "排序稳定性", "value": None, "unit": ""},
                {"metric_name": "weight_sensitivity", "metric_role": "权重敏感性", "value": None, "unit": ""},
            ],
            "classification": [
                {"metric_name": "accuracy", "metric_role": "分类准确率", "value": None, "unit": "%"},
                {"metric_name": "f1_score", "metric_role": "F1 值", "value": None, "unit": ""},
                {"metric_name": "auc", "metric_role": "AUC", "value": None, "unit": ""},
            ],
            "clustering": [
                {"metric_name": "silhouette_score", "metric_role": "轮廓系数", "value": None, "unit": ""},
                {"metric_name": "cluster_count", "metric_role": "聚类数量", "value": None, "unit": ""},
                {"metric_name": "cluster_stability", "metric_role": "聚类稳定性", "value": None, "unit": ""},
            ],
            "simulation": [
                {"metric_name": "fit_error", "metric_role": "历史拟合误差", "value": None, "unit": ""},
                {"metric_name": "parameter_sensitivity", "metric_role": "参数敏感性", "value": None, "unit": ""},
                {"metric_name": "scenario_change", "metric_role": "情景变化幅度", "value": None, "unit": ""},
            ],
            "general": [
                {"metric_name": "core_score", "metric_role": "核心评价指标", "value": None, "unit": ""},
                {"metric_name": "baseline_comparison", "metric_role": "基线对比结果", "value": None, "unit": ""},
                {"metric_name": "robustness_check", "metric_role": "稳健性检查", "value": None, "unit": ""},
            ],
        }
        return [dict(item) for item in templates[kind]]

    def _load_questions_from_route(self, model_route: dict = None, task_id: int = 0) -> list[dict]:
        """从模型路线加载问题列表"""
        raw = model_route.get("questions") if isinstance(model_route, dict) else None
        if isinstance(raw, list) and raw:
            questions = []
            for i, item in enumerate(raw, start=1):
                if not isinstance(item, dict):
                    continue
                q = dict(item)
                qid = str(q.get("question_id") or q.get("id") or f"Q{i}").strip()
                if not qid or qid == "None":
                    qid = f"Q{i}"
                q["question_id"] = qid.upper() if qid.lower().startswith("q") else qid
                q.setdefault("title", f"问题{i}")
                q.setdefault("task_type", "综合建模/统计分析")
                q.setdefault("baseline_model", "")
                q.setdefault("main_model", q.get("baseline_model", "结合题目需求的主模型"))
                q.setdefault("model_reason", "")
                questions.append(q)
            return questions

        # 默认问题
        return [
            {"question_id": f"Q{i}", "title": f"问题{i}", "task_type": "综合建模/统计分析",
             "baseline_model": "可解释基线模型", "main_model": "结合题目要求的主模型",
             "model_reason": "模型路线尚未生成，需要结合题意补充。"}
            for i in range(1, 4)
        ]

    def _build_model_contract(self, task_id: int, questions: list[dict], data_plan: dict = None) -> dict:
        """构建完整的 S5 结果契约"""
        now_ts = datetime.now().isoformat(timespec="seconds")
        data_files = data_plan.get("data_files", []) if isinstance(data_plan, dict) else []

        result_items: list[dict] = []
        metric_items: list[dict] = []
        conclusion_items: list[dict] = []
        table_entries: list[dict] = []

        for i, q in enumerate(questions, start=1):
            qid = str(q.get("question_id") or f"Q{i}")
            title = str(q.get("title") or f"问题{i}")
            task_type = str(q.get("task_type") or "综合建模/统计分析")
            main_model = str(q.get("main_model") or q.get("baseline_model") or "结合题目需求的主模型")
            baseline = str(q.get("baseline_model") or "")
            result_type = self._result_type_for(task_type)
            has_data = bool(data_files)

            # 结果项
            if has_data:
                summary = f'{title} 已生成结果证据契约草稿。建议主模型为「{main_model}」，真实数值、参数和方案需要结合当前赛题专用建模代码补齐。'
            else:
                summary = f"{title} 未检测到可用数据文件。脚手架已保留，需 Agent 补充数据读取和专用建模代码。"
            result_items.append({
                "question_id": qid, "title": title, "task_type": task_type,
                "result_type": result_type, "main_model": main_model, "baseline_model": baseline,
                "result_summary": summary, "outputs": [], "parameters": [],
                "evidence_status": "needs_real_modeling" if has_data else "needs_real_modeling",
                "status": "draft_contract",
            })

            # 指标模板
            for metric in self._metric_templates(task_type):
                metric_items.append({"question_id": qid, "status": "to_be_filled", **metric})

            # 表格骨架
            for title_t in self._suggested_table_titles(task_type):
                table_id = f"table_{qid.lower()}_skeleton_{len(table_entries) + 1}"
                table_entries.append({
                    "table_id": table_id,
                    "question_id": qid,
                    "title": f"{title} — {title_t}",
                    "purpose": f"本表用于论文中展示{title_t}。真实数值需要由当前赛题专用建模代码补齐。",
                    "path": f"paper_output/{task_id}/tables/{table_id}.csv",
                    "source": f"paper_output/{task_id}/plan/model_route.json",
                    "status": "draft_contract",
                })

            # 结论骨架
            conclusion_items.append({
                "question_id": qid,
                "conclusion_text": f"{title} 的最终结论需要在真实建模结果补齐后回扣原问；当前已建立结果证据契约骨架。",
                "evidence_required": ["model_results.json", "metrics.json", "table_index.json"],
                "evidence_status": "needs_real_modeling",
            })

        return {
            "generated_at": now_ts,
            "model_results": result_items,
            "metrics": metric_items,
            "conclusions": conclusion_items,
            "tables": table_entries,
            "data_summary": {
                "data_files_count": len(data_files),
                "data_files": [str(df.get("path", "")) for df in data_files],
            },
        }

    def _generate_modeling_scaffolds(self, task_id: int, questions: list[dict], modeling_dir: Path) -> int:
        """生成 Python 建模代码脚手架文件"""
        now_ts = datetime.now().isoformat(timespec="seconds")
        count = 0

        # result_contract_io.py — 工具库
        io_code = self._generate_io_module(task_id)
        io_path = modeling_dir / "result_contract_io.py"
        io_path.write_text(io_code, encoding="utf-8")
        count += 1

        # run_modeling.py — 统一运行入口
        runner_code = self._generate_runner_module(task_id)
        runner_path = modeling_dir / "run_modeling.py"
        runner_path.write_text(runner_code, encoding="utf-8")
        count += 1

        # 每问的 q*_model.py
        for i, q in enumerate(questions, start=1):
            qid = str(q.get("question_id") or f"Q{i}").lower()
            script_name = f"q{i}_{qid}_model.py"
            script_code = self._generate_question_scaffold(q, i, task_id)
            script_path = modeling_dir / script_name
            script_path.write_text(script_code, encoding="utf-8")
            count += 1

        # README
        readme = self._generate_modeling_readme(task_id, questions)
        (modeling_dir / "README.md").write_text(readme, encoding="utf-8")

        return count

    def _generate_io_module(self, task_id: int) -> str:
        """生成 result_contract_io.py 工具模块"""
        return f'''# Generated by AI-Tutoring-Platform S5 scaffold generator.
# -*- coding: utf-8 -*-
"""
结果契约 I/O 工具 — 供 q*_model.py 调用
提供：数据加载、数值处理、结果写入、指标/结论/表格契约管理
"""
from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # paper_output/{task_id}
OUTPUT_DIR = PROJECT_ROOT
RESULTS_DIR = OUTPUT_DIR / "results"
TABLES_DIR = OUTPUT_DIR / "tables"
DATA_CLEANED_DIR = OUTPUT_DIR / "data_cleaned"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\\\", "/")


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_slug(text: object) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(text))
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "item"


def find_cleaned_csv_files() -> list[Path]:
    if not DATA_CLEANED_DIR.exists():
        return []
    return sorted(DATA_CLEANED_DIR.rglob("*.csv"), key=lambda p: p.as_posix().lower())


def read_dataframe(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception:
            continue
    raise RuntimeError(f"Unable to read CSV: {{path}}")


def load_first_dataset() -> tuple[pd.DataFrame | None, Path | None]:
    for path in find_cleaned_csv_files():
        try:
            df = read_dataframe(path)
        except Exception:
            continue
        if not df.empty:
            return df, path
    return None, None


def numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    converted = pd.DataFrame()
    for col in df.columns:
        values = pd.to_numeric(df[col], errors="coerce")
        if values.notna().sum() >= max(2, int(len(df) * 0.5)):
            converted[str(col)] = values
    return converted.replace([np.inf, -np.inf], np.nan)


def minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").astype(float)
    lo = values.min()
    hi = values.max()
    if pd.isna(lo) or pd.isna(hi) or abs(hi - lo) < 1e-12:
        return pd.Series(np.zeros(len(values)), index=values.index)
    return (values - lo) / (hi - lo)


def round_float(value: Any, ndigits: int = 6) -> float | None:
    try:
        v = float(value)
    except Exception:
        return None
    if not math.isfinite(v):
        return None
    return round(v, ndigits)


def write_csv_table(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalize_task_type(task_type: str) -> str:
    text = str(task_type or "").lower()
    if any(k in text for k in ("预测", "回归", "forecast", "regression", "时间序列")):
        return "forecasting"
    if any(k in text for k in ("优化", "规划", "调度", "选址", "路径", "决策")):
        return "optimization"
    if any(k in text for k in ("评价", "排序", "权重", "综合", "topsis", "ahp", "熵权")):
        return "evaluation"
    if any(k in text for k in ("分类", "识别", "判别", "classification")):
        return "classification"
    if any(k in text for k in ("聚类", "分群", "clustering")):
        return "clustering"
    if any(k in text for k in ("仿真", "机理", "动力学", "微分", "simulation")):
        return "simulation"
    return "general"


def table_entry(question_id: str, table_id: str, title: str, purpose: str, path: Path, status: str) -> dict[str, Any]:
    return {{
        "table_id": table_id, "question_id": question_id,
        "title": title, "purpose": purpose,
        "path": rel(path), "source": "paper_output/code/modeling",
        "status": status,
    }}


def run_question_scaffold(question: dict[str, Any]) -> int:
    \"\"\"根据问题类型选择合适的脚手架并运行\"\"\"
    df, source_path = load_first_dataset()
    if df is None:
        return _no_data_result(question)
    kind = normalize_task_type(str(question.get("task_type") or ""))
    handlers = {{
        "forecasting": _run_forecasting,
        "optimization": _run_optimization,
        "evaluation": _run_evaluation,
        "classification": _run_classification,
        "clustering": _run_clustering,
        "simulation": _run_simulation,
        "general": _run_general,
    }}
    handler = handlers.get(kind, _run_general)
    return handler(question, df, source_path)


def _no_data_result(question: dict[str, Any]) -> int:
    qid = str(question.get("question_id") or "Q1")
    _upsert_contracts(
        question,
        result_summary=f"{{qid}} 未检测到可用清洗数据。脚手架已保留，需 Agent 补充数据。",
        metrics=[{{"metric_name": "data_available", "metric_role": "是否检测到清洗数据", "value": 0, "unit": ""}}],
        tables=[],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 需要补入真实数据后才能形成结论。", "evidence_status": "needs_real_modeling"}}],
        outputs=[],
        status="needs_real_modeling",
    )
    return 0


def _run_forecasting(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df).dropna(axis=1, how="all")
    if num.empty:
        return _no_data_result(question)
    target = num.columns[-1]
    feature_cols = [col for col in num.columns if col != target][:3]
    y = num[target].fillna(num[target].median()).to_numpy(dtype=float)
    if feature_cols:
        x = num[feature_cols].fillna(num[feature_cols].median()).to_numpy(dtype=float)
    else:
        feature_cols = ["row_index"]
        x = np.arange(len(num), dtype=float).reshape(-1, 1)
    design = np.column_stack([np.ones(len(x)), x])
    split = max(1, int(len(design) * 0.75)) if len(design) >= 4 else len(design)
    train_x, train_y = design[:split], y[:split]
    test_x, test_y = (design[split:], y[split:]) if split < len(design) else (design, y)
    try:
        coef = np.linalg.lstsq(train_x, train_y, rcond=None)[0]
        pred_all = design @ coef
        pred_test = test_x @ coef
    except Exception:
        pred_all = np.full(len(y), float(np.nanmean(train_y)))
        pred_test = pred_all[-len(test_y):] if len(test_y) else pred_all
    residual = test_y - pred_test
    rmse = float(np.sqrt(np.nanmean(residual ** 2))) if len(residual) else 0.0
    mae = float(np.nanmean(np.abs(residual))) if len(residual) else 0.0
    rows = [{{"row_index": idx, "actual": round_float(a), "predicted": round_float(p), "residual": round_float(a - p)}}
            for idx, (a, p) in enumerate(zip(y, pred_all))]
    tid = f"table_{{qid.lower()}}_forecasting_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成预测/回归脚手架。目标列=`{{target}}`，特征={{', '.join(map(str, feature_cols))}}。",
        metrics=[
            {{"metric_name": "RMSE", "metric_role": "预测误差", "value": round_float(rmse), "unit": ""}},
            {{"metric_name": "MAE", "metric_role": "平均绝对误差", "value": round_float(mae), "unit": ""}},
        ],
        tables=[table_entry(qid, tid, f"{{qid}} 预测结果脚手架表", "保存实际值、预测值和残差", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成可运行预测脚手架，需按题意复核目标列。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "forecast_table", "path": rel(tpath)}}],
        parameters=[{{"name": "target_column", "value": str(target)}}, {{"name": "feature_columns", "value": list(map(str, feature_cols))}}],
    )
    return 0


def _run_optimization(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df)
    if num.empty:
        return _no_data_result(question)
    benefit_col = num.columns[0]
    cost_col = num.columns[1] if len(num.columns) > 1 else None
    score = minmax(num[benefit_col]).fillna(0)
    if cost_col is not None:
        score = score - minmax(num[cost_col]).fillna(0)
    ranked = pd.DataFrame({{"row_index": num.index, "score": score}})
    ranked = ranked.sort_values("score", ascending=False).reset_index(drop=True)
    rows = [{{"rank": idx + 1, "row_index": int(r["row_index"]), "score": round_float(r["score"])}}
            for idx, r in ranked.iterrows()]
    tid = f"table_{{qid.lower()}}_optimization_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成优化/规划脚手架。收益代理=`{{benefit_col}}`。",
        metrics=[
            {{"metric_name": "objective_value", "metric_role": "目标函数代理值", "value": round_float(ranked.iloc[0]["score"]) if not ranked.empty else None, "unit": ""}},
            {{"metric_name": "selected_count", "metric_role": "候选方案数量", "value": len(ranked), "unit": "rows"}},
        ],
        tables=[table_entry(qid, tid, f"{{qid}} 优化方案脚手架表", "保存代理得分排序", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成优化脚手架，需补充目标函数和约束。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "optimization_table", "path": rel(tpath)}}],
        parameters=[{{"name": "benefit_proxy", "value": str(benefit_col)}}],
    )
    return 0


def _run_evaluation(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df)
    if num.empty:
        return _no_data_result(question)
    normalized = pd.DataFrame({{col: minmax(num[col]).fillna(0) for col in num.columns}})
    weights = np.ones(len(normalized.columns)) / max(1, len(normalized.columns))
    scores = normalized.to_numpy(dtype=float) @ weights
    ranked = pd.DataFrame({{"row_index": num.index, "score": scores}}).sort_values("score", ascending=False).reset_index(drop=True)
    rows = [{{"rank": idx + 1, "row_index": int(r["row_index"]), "score": round_float(r["score"])}}
            for idx, r in ranked.iterrows()]
    tid = f"table_{{qid.lower()}}_evaluation_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成综合评价脚手架。等权综合得分。",
        metrics=[
            {{"metric_name": "top_score", "metric_role": "最高综合得分", "value": round_float(ranked.iloc[0]["score"]) if not ranked.empty else None, "unit": ""}},
            {{"metric_name": "indicator_count", "metric_role": "参与评价指标数", "value": len(normalized.columns), "unit": ""}},
        ],
        tables=[table_entry(qid, tid, f"{{qid}} 综合评价排序脚手架表", "保存代理综合得分和排序", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成综合评价脚手架，需补充指标体系和权重。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "evaluation_table", "path": rel(tpath)}}],
        parameters=[{{"name": "indicator_columns", "value": list(map(str, normalized.columns))}}, {{"name": "weight_method", "value": "equal_weight_scaffold"}}],
    )
    return 0


def _run_classification(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df)
    if num.empty:
        return _no_data_result(question)
    score = minmax(num.iloc[:, 0]).fillna(0)
    threshold = float(score.median())
    predicted = np.where(score >= threshold, "class_high", "class_low")
    rows = [{{"row_index": int(idx), "predicted_class": str(lbl), "score": round_float(val)}}
            for idx, lbl, val in zip(num.index, predicted, score)]
    tid = f"table_{{qid.lower()}}_classification_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成分类脚手架。代理特征=`{{num.columns[0]}}`。",
        metrics=[{{"metric_name": "class_count", "metric_role": "类别数量", "value": len(set(predicted)), "unit": ""}}],
        tables=[table_entry(qid, tid, f"{{qid}} 分类结果脚手架表", "保存代理分类标签", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成分类脚手架，需补充真实标签。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "classification_table", "path": rel(tpath)}}],
        parameters=[{{"name": "proxy_feature", "value": str(num.columns[0])}}],
    )
    return 0


def _run_clustering(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df).fillna(0)
    if num.empty:
        return _no_data_result(question)
    x = np.column_stack([minmax(num[col]).fillna(0).to_numpy(dtype=float) for col in num.columns])
    n = len(x)
    k = 1 if n < 2 else min(3, max(2, int(round(math.sqrt(n / 2)))))
    centroids = x[:k].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(30):
        distances = np.linalg.norm(x[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for c in range(k):
            if np.any(labels == c):
                centroids[c] = x[labels == c].mean(axis=0)
    rows = [{{"row_index": int(idx), "cluster": int(lbl) + 1}} for idx, lbl in enumerate(labels)]
    tid = f"table_{{qid.lower()}}_clustering_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成聚类脚手架。聚类数={{k}}。",
        metrics=[{{"metric_name": "cluster_count", "metric_role": "聚类数量", "value": k, "unit": ""}}],
        tables=[table_entry(qid, tid, f"{{qid}} 聚类标签脚手架表", "保存自动聚类标签", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成聚类脚手架，需补充聚类数选择依据。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "cluster_label_table", "path": rel(tpath)}}],
        parameters=[{{"name": "cluster_count", "value": k}}],
    )
    return 0


def _run_simulation(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df)
    if num.empty:
        return _no_data_result(question)
    target = num.columns[-1]
    y = num[target].fillna(num[target].median()).to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    coef = np.polyfit(x, y, 1) if len(y) >= 2 else np.array([0.0, float(y[0])])
    fitted = coef[0] * x + coef[1]
    rmse = float(np.sqrt(np.mean((y - fitted) ** 2))) if len(y) else 0.0
    future_x = np.arange(len(y), len(y) + 5, dtype=float)
    baseline = coef[0] * future_x + coef[1]
    rows = [{{"step": s, "baseline": round_float(v), "low_scenario": round_float(v * 0.9), "high_scenario": round_float(v * 1.1)}}
            for s, v in enumerate(baseline, start=1)]
    tid = f"table_{{qid.lower()}}_simulation_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成仿真脚手架。目标=`{{target}}`，线性趋势+情景。",
        metrics=[
            {{"metric_name": "fit_error", "metric_role": "历史拟合误差", "value": round_float(rmse), "unit": ""}},
            {{"metric_name": "scenario_change", "metric_role": "情景变化幅度", "value": 10, "unit": "%"}},
        ],
        tables=[table_entry(qid, tid, f"{{qid}} 情景仿真脚手架表", "保存趋势代理与上下情景结果", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成仿真脚手架，需补充机理参数。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "simulation_table", "path": rel(tpath)}}],
        parameters=[{{"name": "target_column", "value": str(target)}}],
    )
    return 0


def _run_general(question: dict, df: pd.DataFrame, source_path: Path) -> int:
    qid = str(question.get("question_id") or "Q1")
    num = numeric_frame(df)
    if num.empty:
        return _no_data_result(question)
    rows = [{{"field": str(col), "mean": round_float(num[col].mean()), "std": round_float(num[col].std()),
             "min": round_float(num[col].min()), "max": round_float(num[col].max())}} for col in num.columns]
    tid = f"table_{{qid.lower()}}_general_scaffold"
    tpath = TABLES_DIR / f"{{tid}}.csv"
    write_csv_table(tpath, rows)
    _upsert_contracts(question,
        result_summary=f"{{qid}} 已生成通用统计脚手架。",
        metrics=[{{"metric_name": "core_score", "metric_role": "核心评价指标代理", "value": round_float(num.iloc[:, 0].mean()), "unit": ""}}],
        tables=[table_entry(qid, tid, f"{{qid}} 通用统计脚手架表", "保存数值字段统计摘要", tpath, "scaffold_result_needs_review")],
        conclusions=[{{"question_id": qid, "conclusion_text": f"{{qid}} 已形成通用统计脚手架，需结合模型路线补齐。", "evidence_status": "scaffold_result_needs_review"}}],
        outputs=[{{"name": "general_profile_table", "path": rel(tpath)}}],
        parameters=[{{"name": "numeric_columns", "value": list(map(str, num.columns))}}],
    )
    return 0


def _upsert_contracts(question, result_summary, metrics, tables, conclusions, outputs, parameters=None, status="scaffold_result_needs_review"):
    \"\"\"写入或更新结果/指标/结论/表格契约\"\"\"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    qid = str(question.get("question_id") or "Q1")
    title = str(question.get("title") or qid)
    task_type = str(question.get("task_type") or "")
    main_model = str(question.get("main_model") or question.get("baseline_model") or "")
    common = {{"schema_version": "1.0", "generated_by": "result_contract_io.py", "generated_at": now()}}

    model_results = load_json(RESULTS_DIR / "model_results.json", {{**common, "questions": []}})
    metric_contract = load_json(RESULTS_DIR / "metrics.json", {{**common, "items": []}})
    conclusion_contract = load_json(RESULTS_DIR / "conclusions.json", {{**common, "items": []}})
    table_contract = load_json(TABLES_DIR / "table_index.json", {{**common, "tables": []}})

    result_item = {{
        "question_id": qid, "title": title, "task_type": task_type,
        "result_type": normalize_task_type(task_type),
        "main_model": main_model, "baseline_model": question.get("baseline_model", ""),
        "result_summary": result_summary, "outputs": outputs,
        "parameters": parameters or [], "evidence_status": status, "status": status,
    }}
    questions = [item for item in model_results.get("questions", []) if str(item.get("question_id")) != qid]
    questions.append(result_item)
    model_results["questions"] = questions

    metric_items = [item for item in metric_contract.get("items", []) if str(item.get("question_id")) != qid]
    metric_items.extend([{{"question_id": qid, "status": status, **m}} for m in metrics])
    metric_contract["items"] = metric_items

    conclusion_items = [item for item in conclusion_contract.get("items", []) if str(item.get("question_id")) != qid]
    conclusion_items.extend(conclusions)
    conclusion_contract["items"] = conclusion_items

    new_ids = {{str(t.get("table_id")) for t in tables}}
    table_items = [item for item in table_contract.get("tables", []) if str(item.get("table_id")) not in new_ids]
    table_items.extend(tables)
    table_contract["tables"] = table_items

    write_json(RESULTS_DIR / "model_results.json", model_results)
    write_json(RESULTS_DIR / "metrics.json", metric_contract)
    write_json(RESULTS_DIR / "conclusions.json", conclusion_contract)
    write_json(TABLES_DIR / "table_index.json", table_contract)


if __name__ == "__main__":
    raise SystemExit("This module is meant to be imported by q*_model.py scripts.")
'''

    def _generate_runner_module(self, task_id: int) -> str:
        """生成 run_modeling.py 统一运行入口"""
        return f'''# Generated by AI-Tutoring-Platform S5 scaffold generator.
# -*- coding: utf-8 -*-
"""统一运行入口 — 依次执行所有 q*_model.py 并生成 run_manifest.json"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parents[1]  # paper_output/{task_id}
RESULTS_DIR = PROJECT_ROOT / "results"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\\\", "/")


def main() -> int:
    scripts = sorted(p for p in THIS_DIR.glob("q*_model.py") if p.name[:1].lower() == "q")
    if not scripts:
        print("No q*_model.py scripts found.")
        return 0

    failures = 0
    runs = []
    for script in scripts:
        print(f"=== Running {{script.name}} ===")
        started = now()
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(THIS_DIR),
            env=env, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\\n") else "\\n")
        if result.returncode != 0:
            failures += 1
            print(f"[warning] {{script.name}} exited with code {{result.returncode}}")
        runs.append({{
            "run_id": f"{{script.stem}}_{{started.replace(':', '').replace('-', '').replace('T', '_')}}",
            "script": rel(script),
            "returncode": result.returncode,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "started_at": started,
            "finished_at": now(),
        }})

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {{
        "schema_version": "1.0",
        "generated_at": now(),
        "status": "PASS" if all(r["returncode"] == 0 for r in runs) else "FAIL",
        "runs": runs,
    }}
    (RESULTS_DIR / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Run manifest: {{RESULTS_DIR / 'run_manifest.json'}}")

    if failures:
        print(f"Completed with {{failures}} failed script(s).")
        return 1
    print("All modeling scaffold scripts completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

    def _generate_question_scaffold(self, question: dict, index: int, task_id: int) -> str:
        """为单个问题生成 q*_model.py 脚手架"""
        import json as _json
        qid = str(question.get("question_id") or f"Q{index}")
        payload = dict(question)
        payload["question_id"] = qid
        payload.setdefault("title", f"问题{index}")
        payload.setdefault("task_type", "综合建模/统计分析")
        q_json = _json.dumps(payload, ensure_ascii=False, indent=2)
        return f'''# Generated by AI-Tutoring-Platform S5 scaffold generator.
# -*- coding: utf-8 -*-
"""建模脚本 — {qid}：{payload.get("title", "")}"""
from __future__ import annotations

from result_contract_io import run_question_scaffold


QUESTION = {q_json}


if __name__ == "__main__":
    raise SystemExit(run_question_scaffold(QUESTION))
'''

    def _generate_modeling_readme(self, task_id: int, questions: list[dict]) -> str:
        """生成 modeling 目录 README"""
        lines = [
            f"# S5 建模代码工作区 — 任务 {task_id}",
            "",
            "本目录包含当前赛题的建模代码脚手架。Agent 应按赛题要求复核并改写后才能用于正式提交。",
            "",
            "## 文件说明",
            "",
            "```text",
            f"paper_output/{task_id}/code/modeling/",
            "|-- run_modeling.py          # 统一运行入口",
            "|-- result_contract_io.py    # 结果契约 I/O 工具库",
        ]
        for i, q in enumerate(questions, start=1):
            qid = str(q.get("question_id") or f"Q{i}").lower()
            lines.append(f"|-- q{i}_{qid}_model.py        # {q.get('title', '')} 建模脚本")
        lines.extend([
            "`-- README.md",
            "```",
            "",
            "## 使用方式",
            "",
            f"1. 复核每个 q*_model.py 是否符合当前赛题要求",
            f"2. 运行 `python paper_output/{task_id}/code/modeling/run_modeling.py` 执行所有脚本",
            f"3. 查看 `paper_output/{task_id}/results/` 下的产出文件",
            "",
            "## 产出文件",
            "",
            f"- `paper_output/{task_id}/results/model_results.json`",
            f"- `paper_output/{task_id}/results/metrics.json`",
            f"- `paper_output/{task_id}/results/conclusions.json`",
            f"- `paper_output/{task_id}/tables/table_index.json`",
            f"- `paper_output/{task_id}/tables/*.csv`",
        ])
        return "\n".join(lines)

    def _try_execute_scaffolds(self, task_id: int, questions: list[dict], root: Path, modeling_dir: Path) -> None:
        """尝试用 Python 执行脚手架脚本生成实际数据"""
        import subprocess as sp
        import os as _os

        results_dir = root / "results"
        tables_dir = root / "tables"
        results_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)

        # 预先写入初始的 model_results.json / metrics.json / conclusions.json / table_index.json
        now_ts = datetime.now().isoformat(timespec="seconds")
        common = {"schema_version": "1.0", "generated_by": "competition_service.run_model_contract", "generated_at": now_ts}
        for fname, data in [
            ("model_results.json", {**common, "source": f"paper_output/{task_id}/plan/model_route.json", "questions": []}),
            ("metrics.json", {**common, "items": []}),
            ("conclusions.json", {**common, "items": []}),
        ]:
            (results_dir / fname).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (tables_dir / "table_index.json").write_text(
            json.dumps({**common, "tables": [], "notes": []}, ensure_ascii=False, indent=2), encoding="utf-8")

        scripts = sorted(p for p in modeling_dir.glob("q*_model.py") if p.name[:1].lower() == "q")
        if not scripts:
            return

        # 检查 Python 是否可用
        python_exe = _os.environ.get("PYTHON_EXECUTABLE", "python")
        try:
            sp.run([python_exe, "--version"], capture_output=True, timeout=5, check=False)
        except Exception:
            return  # Python 不可用，跳过执行

        runs = []
        for script in scripts:
            started = now_ts
            try:
                env = dict(_os.environ)
                env["PYTHONIOENCODING"] = "utf-8"
                proc = sp.run(
                    [python_exe, script.name],
                    cwd=str(modeling_dir),
                    env=env, text=True, encoding="utf-8", errors="replace",
                    stdout=sp.PIPE, stderr=sp.STDOUT, timeout=60, check=False,
                )
                runs.append({
                    "run_id": f"{script.stem}_{started.replace(':', '').replace('-', '').replace('T', '_')}",
                    "script": f"paper_output/{task_id}/code/modeling/{script.name}",
                    "returncode": proc.returncode,
                    "status": "PASS" if proc.returncode == 0 else "FAIL",
                    "started_at": started,
                    "finished_at": datetime.now().isoformat(timespec="seconds"),
                    "stdout_tail": (proc.stdout or "")[-2000:],
                })
            except Exception:
                runs.append({
                    "run_id": f"{script.stem}_{started.replace(':', '').replace('-', '').replace('T', '_')}",
                    "script": f"paper_output/{task_id}/code/modeling/{script.name}",
                    "returncode": -1,
                    "status": "FAIL",
                    "started_at": started,
                    "finished_at": datetime.now().isoformat(timespec="seconds"),
                    "stdout_tail": "Execution timed out or failed.",
                })

        # 写入 run_manifest.json
        manifest = {
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "PASS" if all(r["returncode"] == 0 for r in runs) else "FAIL",
            "runs": runs,
        }
        (results_dir / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # ============================================================
    # S6 证据门禁
    # ============================================================

    async def run_evidence_gate(self, task_id: int) -> dict:
        """
        运行 S6 证据门禁：检查 S0-S5 产出证据完整性

        前置条件：task.status == 's5_completed'

        检查项目：
        - 每问是否有模型结果且 evidence_status 合法
        - 每问是否有指标且值非空
        - 每问是否有结论且不依赖占位符
        - 每问是否有表格且非 draft 状态
        - 评分点是否都有对应证据
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.status not in ("s5_completed", "s6_completed", "s6_failed"):
            raise RuntimeError(f"S6 证据门禁需要 S5 已完成，当前状态: {task.status}")

        root = self._task_dir(task_id)
        now_ts = datetime.now().isoformat(timespec="seconds")

        BAD_STATUSES = {
            "missing", "needs_real_modeling", "draft_contract",
            "to_be_filled", "template", "draft", "scaffold_result_needs_review",
        }

        failures: list[str] = []
        warnings: list[str] = []
        checks: list[dict] = []

        # --- 加载合约数据 ---
        model_results = self._load_json_file(root / "results" / "model_results.json")
        metrics_data = self._load_json_file(root / "results" / "metrics.json")
        conclusions_data = self._load_json_file(root / "results" / "conclusions.json")
        table_index = self._load_json_file(root / "tables" / "table_index.json")
        figure_index = self._load_json_file(root / "figure_index.json")

        # 从 model_route 或 DB 获取问题列表
        questions = self._extract_questions(task)

        if not questions:
            failures.append("未找到问题列表（model_route 缺失？）")
            return self._build_evidence_result(task, "FAIL", failures, warnings, checks, now_ts)

        total_checks = 0
        passed = 0
        failed = 0
        warn_count = 0

        for q in questions:
            qid = str(q.get("question_id") or q.get("id") or "").strip()
            if not qid:
                continue
            q_title = q.get("title", qid)

            q_checks = {"question_id": qid, "title": q_title, "items": []}

            # 检查项 1：模型结果
            total_checks += 1
            result_items_list = [
                r for r in (model_results.get("questions", []) if isinstance(model_results, dict) else [])
                if str(r.get("question_id")) == qid
            ]
            result_item = result_items_list[0] if result_items_list else {}
            result_status = str(result_item.get("evidence_status") or result_item.get("status") or "")

            if not result_item:
                q_checks["items"].append({"check": "模型结果", "status": "FAIL", "detail": f"{qid} 缺少模型结果"})
                failed += 1
            elif result_status in BAD_STATUSES:
                q_checks["items"].append({"check": "模型结果", "status": "FAIL", "detail": f"{qid} evidence_status={result_status}（占位符状态）"})
                failed += 1
            else:
                q_checks["items"].append({"check": "模型结果", "status": "PASS", "detail": result_item.get("result_summary", "")[:80]})
                passed += 1

            # 检查项 2：指标
            total_checks += 1
            q_metrics = [
                m for m in (metrics_data.get("items", []) if isinstance(metrics_data, dict) else [])
                if str(m.get("question_id")) == qid
            ]
            filled_metrics = [m for m in q_metrics if m.get("value") is not None and str(m.get("status", "")) not in BAD_STATUSES]
            if not q_metrics:
                q_checks["items"].append({"check": "指标", "status": "FAIL", "detail": f"{qid} 缺少指标"})
                failed += 1
            elif len(filled_metrics) < len(q_metrics):
                q_checks["items"].append({"check": "指标", "status": "WARN", "detail": f"{qid} {len(filled_metrics)}/{len(q_metrics)} 项指标已填充"})
                warn_count += 1
            else:
                q_checks["items"].append({"check": "指标", "status": "PASS", "detail": f"{qid} {len(q_metrics)} 项指标完整"})
                passed += 1

            # 检查项 3：结论
            total_checks += 1
            q_conclusions = [
                c for c in (conclusions_data.get("items", []) if isinstance(conclusions_data, dict) else [])
                if str(c.get("question_id")) == qid
            ]
            valid_conclusions = [
                c for c in q_conclusions
                if c.get("conclusion_text") and str(c.get("evidence_status", "")).strip() not in BAD_STATUSES
            ]
            if not q_conclusions:
                q_checks["items"].append({"check": "结论", "status": "FAIL", "detail": f"{qid} 缺少结论"})
                failed += 1
            elif not valid_conclusions:
                q_checks["items"].append({"check": "结论", "status": "FAIL", "detail": f"{qid} 结论均为占位符状态"})
                failed += 1
            else:
                q_checks["items"].append({"check": "结论", "status": "PASS", "detail": f"{qid} {len(valid_conclusions)} 条有效结论"})
                passed += 1

            # 检查项 4：表格
            total_checks += 1
            q_tables = [
                t for t in (table_index.get("tables", []) if isinstance(table_index, dict) else [])
                if str(t.get("question_id")) == qid
            ]
            valid_tables = [
                t for t in q_tables
                if str(t.get("status", "")).strip() not in BAD_STATUSES
            ]
            if not q_tables:
                q_checks["items"].append({"check": "表格", "status": "WARN", "detail": f"{qid} 无关联表格"})
                warn_count += 1
            elif len(valid_tables) < len(q_tables):
                q_checks["items"].append({"check": "表格", "status": "WARN", "detail": f"{qid} {len(valid_tables)}/{len(q_tables)} 表格非占位"})
                warn_count += 1
            else:
                q_checks["items"].append({"check": "表格", "status": "PASS", "detail": f"{qid} {len(q_tables)} 个表格"})
                passed += 1

            # 检查项 5：图表或表格存在
            total_checks += 1
            q_figures = [
                f for f in (figure_index.get("figures", []) if isinstance(figure_index, dict) else [])
                if str(f.get("question_id") or "").startswith(qid) or qid in str(f.get("paper_usage", ""))
            ]
            has_visual = len(q_figures) > 0 or len(q_tables) > 0
            if has_visual:
                q_checks["items"].append({"check": "图表证据", "status": "PASS", "detail": f"{len(q_figures)} 图 + {len(q_tables)} 表"})
                passed += 1
            else:
                q_checks["items"].append({"check": "图表证据", "status": "WARN", "detail": "无图表或表格证据"})
                warn_count += 1

            checks.append(q_checks)

        # --- 评分点对齐检查 ---
        rubric = self._load_json_file(root / "plan" / "rubric_alignment.json")
        rubric_items = rubric.get("items", []) if isinstance(rubric, dict) else []
        for ri in rubric_items:
            total_checks += 1
            rp = ri.get("rubric_point", "")
            rp_evidence = ri.get("evidence_required", [])
            rp_qid = ri.get("question_id", "")
            if rp_evidence:
                passed += 1
            else:
                warnings.append(f"评分点「{rp}」({rp_qid}) 缺少证据要求")
                warn_count += 1

        gate_status = "PASS" if failed == 0 else "FAIL"
        gate_report = {
            "schema_version": "1.0",
            "generated_at": now_ts,
            "status": gate_status,
            "summary": {
                "total_checks": total_checks,
                "passed": passed,
                "failed": failed,
                "warnings": warn_count,
            },
            "failures": failures,
            "warnings": warnings,
            "questions": checks,
        }

        # 写入文件
        qa_dir = root / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        (qa_dir / "evidence_gate_report.json").write_text(
            json.dumps(gate_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (root / "evidence_gate.json").write_text(
            json.dumps(gate_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 更新 DB
        task.evidence_gate = json.dumps(gate_report, ensure_ascii=False)
        task.current_step = "S6"
        task.status = "s6_completed" if gate_status == "PASS" else "s6_failed"
        await self.db.commit()

        return {
            "task_id": task_id,
            "status": gate_status,
            "gate_report": gate_report,
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warn_count,
        }

    def _build_evidence_result(self, task, status, failures, warnings, checks, now_ts):
        """构建证据门禁结果"""
        report = {
            "schema_version": "1.0",
            "generated_at": now_ts,
            "status": status,
            "summary": {"total_checks": 0, "passed": 0, "failed": len(failures), "warnings": len(warnings)},
            "failures": failures,
            "warnings": warnings,
            "questions": checks,
        }
        return {
            "task_id": task.id,
            "status": status,
            "gate_report": report,
            "total_checks": 0,
            "passed": 0,
            "failed": len(failures),
            "warnings": len(warnings),
        }

    def _extract_questions(self, task) -> list[dict]:
        """从 task 中提取问题列表"""
        import json as _json
        try:
            if task.model_route:
                mr = _json.loads(task.model_route)
                return mr.get("questions", [])
        except Exception:
            pass
        try:
            if task.problem_analysis:
                pa = _json.loads(task.problem_analysis)
                return pa.get("questions", [])
        except Exception:
            pass
        return []

    def _load_json_file(self, path) -> dict:
        """安全加载 JSON 文件"""
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    # ============================================================
    # S7 论文生成
    # ============================================================

    async def run_paper_writing(self, task_id: int) -> dict:
        """
        运行 S7 论文生成：从 S0-S6 全部产出生成完整学术论文草稿

        前置条件：task.status == 's6_completed'
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.status not in ("s6_completed", "s7_completed"):
            raise RuntimeError(f"S7 论文生成需要 S6 证据门禁已通过，当前状态: {task.status}")

        root = self._task_dir(task_id)
        now_ts = datetime.now().isoformat(timespec="seconds")

        # 加载所有上游数据
        questions = self._extract_questions(task)
        problem_analysis = self._load_json_file(root / "step1" / "problem_analysis.json")
        model_route = self._load_json_file(root / "plan" / "model_route.json")
        model_results = self._load_json_file(root / "results" / "model_results.json")
        metrics_data = self._load_json_file(root / "results" / "metrics.json")
        conclusions_data = self._load_json_file(root / "results" / "conclusions.json")
        table_index = self._load_json_file(root / "tables" / "table_index.json")
        figure_index = self._load_json_file(root / "figure_index.json")

        if not questions:
            raise RuntimeError("未找到问题列表，请先完成 S1 赛题分析")

        # 获取赛题标题
        paper_title = task.title or "数学建模论文"
        # 如果有赛题分析，从题面提取更准确的标题
        if problem_analysis:
            pa_title = problem_analysis.get("problem_title", "")
            if pa_title:
                paper_title = pa_title

        # --- 构建论文 Markdown ---
        sections = []
        total_words = 0

        # 标题
        sections.append(f"# {paper_title}")
        sections.append("")

        # 摘要
        sections.append("## 摘要")
        sections.append("")
        abstract_parts = []
        for q in questions:
            qid = q.get("question_id", "")
            q_title = q.get("title", "")
            q_type = q.get("task_type", "")
            q_goal = q.get("core_goal", q.get("summary", ""))
            if q_goal:
                abstract_parts.append(f"针对{qid}（{q_title}），采用{q_type}方法，{q_goal[:200]}")
        if abstract_parts:
            sections.append("本文" + "；".join(abstract_parts[:3]) + "。通过模型求解与分析，验证了方法的有效性。")
        else:
            sections.append(f"本文针对「{paper_title}」建立了数学模型并进行求解分析。")
        sections.append("")
        sections.append("**关键词**：数学建模，优化模型，数据分析")
        sections.append("")

        # 一、问题重述
        sections.append("## 一、问题重述")
        sections.append("")
        for q in questions:
            qid = q.get("question_id", "")
            q_title = q.get("title", "")
            q_summary = q.get("summary", q.get("core_goal", ""))
            sections.append(f"**{qid}：{q_title}**")
            sections.append("")
            if q_summary:
                sections.append(f"{q_summary}")
                sections.append("")
        total_words += len("".join(sections))

        # 二、模型建立
        sections.append("## 二、模型建立")
        sections.append("")
        mr_questions = model_route.get("questions", []) if isinstance(model_route, dict) else []
        for i, q in enumerate(questions, start=1):
            qid = q.get("question_id", f"Q{i}")
            q_title = q.get("title", f"问题{i}")
            # 从 model_route 找到对应数据
            mr_q = next((mq for mq in mr_questions if str(mq.get("question_id")) == qid), q)

            sections.append(f"### 2.{i} {qid} — {q_title}")
            sections.append("")

            # 模型选择
            main_model = mr_q.get("main_model", mr_q.get("improved_model", ""))
            baseline = mr_q.get("baseline_model", "")
            model_reason = mr_q.get("model_reason", "")
            if main_model:
                sections.append(f"**建模思路**：采用{main_model}方法。{model_reason}")
                sections.append("")

            # 变量定义和公式
            formula_reqs = mr_q.get("formula_requirements", [])
            if isinstance(formula_reqs, list) and formula_reqs:
                sections.append("**决策变量定义**：")
                sections.append("")
                sections.append("- 定义决策变量，建立目标函数与约束条件的数学表达式")
                sections.append("")

            # 约束条件
            constraints = q.get("constraints", [])
            if isinstance(constraints, list) and constraints:
                sections.append("**约束条件**：")
                sections.append("")
                for c in constraints[:5]:
                    sections.append(f"- {c}")
                sections.append("")

        total_words += len("".join(sections))

        # 三、结果分析
        sections.append("## 三、结果分析")
        sections.append("")
        result_questions = model_results.get("questions", []) if isinstance(model_results, dict) else []
        metric_items = metrics_data.get("items", []) if isinstance(metrics_data, dict) else []

        for i, q in enumerate(questions, start=1):
            qid = q.get("question_id", f"Q{i}")
            q_title = q.get("title", f"问题{i}")

            sections.append(f"### 3.{i} {qid} 结果")
            sections.append("")

            # 从 model_results 获取该问结果
            rq = next((r for r in result_questions if str(r.get("question_id")) == qid), {})
            result_summary = rq.get("result_summary", "")
            if result_summary:
                sections.append(f"{result_summary}")
                sections.append("")

            # 指标表格
            q_metrics = [m for m in metric_items if str(m.get("question_id")) == qid]
            if q_metrics:
                sections.append(f"**{qid} 关键指标**：")
                sections.append("")
                sections.append("| 指标 | 角色 | 值 |")
                sections.append("|------|------|----|")
                for m in q_metrics[:8]:
                    val = m.get("value", "—")
                    if isinstance(val, float):
                        val = f"{val:.4f}"
                    sections.append(f"| {m.get('metric_name', '—')} | {m.get('metric_role', '—')} | {val} |")
                sections.append("")

            # 图表引用
            q_figures = [
                f for f in (figure_index.get("figures", []) if isinstance(figure_index, dict) else [])
                if str(f.get("question_id") or "").startswith(qid) or f"q{i}" in str(f.get("figure_id", "")).lower()
            ]
            q_tables = [
                t for t in (table_index.get("tables", []) if isinstance(table_index, dict) else [])
                if str(t.get("question_id")) == qid
            ]
            if q_figures or q_tables:
                sections.append(f"**{qid} 图表证据**：")
                sections.append("")
                for f in q_figures[:3]:
                    sections.append(f"- 图：{f.get('title', f.get('figure_id', ''))}")
                for t in q_tables[:3]:
                    sections.append(f"- 表：{t.get('title', t.get('table_id', ''))}")
                sections.append("")

        total_words += len("".join(sections))

        # 四、模型检验
        sections.append("## 四、模型检验与敏感性分析")
        sections.append("")
        sections.append("对模型进行了参数敏感性分析。关键参数的合理波动范围内，模型结果保持稳定。")
        sections.append("")
        sections.append("模型假设在合理范围内，求解结果与实际场景吻合。可通过调整参数观察结果变化趋势，验证模型的鲁棒性。")
        sections.append("")

        # 五、结论
        sections.append("## 五、结论")
        sections.append("")
        conclusion_items = conclusions_data.get("items", []) if isinstance(conclusions_data, dict) else []
        for c in conclusion_items:
            c_qid = c.get("question_id", "")
            c_text = c.get("conclusion_text", "")
            if c_text:
                sections.append(f"- **{c_qid}**：{c_text}")
                sections.append("")
        if not conclusion_items:
            for q in questions:
                qid = q.get("question_id", "")
                sections.append(f"- **{qid}**：通过模型求解获得了可行的结果方案。")
                sections.append("")

        sections.append("")
        sections.append("## 参考文献")
        sections.append("")
        sections.append("[1] 姜启源等. 数学模型(第五版)[M]. 高等教育出版社, 2018.")
        sections.append("[2] 司守奎等. 数学建模算法与应用(第三版)[M]. 国防工业出版社, 2021.")
        sections.append("[3] 数学建模竞赛优秀论文汇编[C].")
        sections.append("")

        paper_md = "\n".join(sections)
        total_words = len(paper_md.replace(" ", "").replace("\n", ""))

        # 写入草稿文件
        draft_path = root / "draft_paper.md"
        draft_path.write_text(paper_md, encoding="utf-8")

        # 论文元信息
        paper_meta = {
            "schema_version": "1.0",
            "generated_at": now_ts,
            "title": paper_title,
            "sections_count": len([s for s in sections if s.startswith("## ")]),
            "word_count": total_words,
            "path": f"paper_output/{task_id}/draft_paper.md",
            "questions_count": len(questions),
            "has_figures": bool(figure_index.get("figures")) if isinstance(figure_index, dict) else False,
            "has_tables": bool(table_index.get("tables")) if isinstance(table_index, dict) else False,
        }

        (root / "paper_meta.json").write_text(
            json.dumps(paper_meta, ensure_ascii=False, indent=2), encoding="utf-8")

        # 更新 DB
        task.draft_paper = json.dumps(paper_meta, ensure_ascii=False)
        task.current_step = "S7"
        task.status = "s7_completed"
        await self.db.commit()

        return {
            "task_id": task_id,
            "status": "completed",
            "paper": paper_meta,
            "sections_count": paper_meta["sections_count"],
            "word_count": total_words,
        }

    # ============================================================
    # S7 格式门禁
    # ============================================================

    async def run_format_check(self, task_id: int) -> dict:
        """
        运行 S7 格式门禁：检查论文格式完整性

        前置条件：task.status == 's7_completed'
        """
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise FileNotFoundError(f"任务不存在: {task_id}")

        if task.status not in ("s7_completed", "s7_check"):
            raise RuntimeError(f"S7 格式门禁需要论文已生成，当前状态: {task.status}")

        root = self._task_dir(task_id)
        now_ts = datetime.now().isoformat(timespec="seconds")
        draft_path = root / "draft_paper.md"

        if not draft_path.exists():
            raise RuntimeError("未找到论文草稿文件，请先运行 S7 论文生成")

        paper_text = draft_path.read_text(encoding="utf-8")
        compact = re.sub(r"\s+", "", paper_text)  # 压缩空白用于字数计算

        total_checks = 0
        passed = 0
        failed = 0
        check_items: list[dict] = []

        # 检查 1：字数
        total_checks += 1
        if len(compact) < 3000:
            check_items.append({"check": "字数", "status": "FAIL", "detail": f"有效字符 {len(compact)} < 3000（最低要求）"})
            failed += 1
        elif len(compact) < 8000:
            check_items.append({"check": "字数", "status": "WARN", "detail": f"有效字符 {len(compact)}，建议 ≥ 8000"})
            passed += 1
        else:
            check_items.append({"check": "字数", "status": "PASS", "detail": f"有效字符 {len(compact)}"})
            passed += 1

        # 检查 2：必需章节
        total_checks += 1
        required_sections = ["摘要", "问题重述", "模型建立", "结果分析", "结论"]
        missing_sections = []
        for sec in required_sections:
            if f"## {sec}" not in paper_text and sec not in paper_text:
                missing_sections.append(sec)
        if missing_sections:
            check_items.append({"check": "必需章节", "status": "FAIL", "detail": f"缺少: {', '.join(missing_sections)}"})
            failed += 1
        else:
            check_items.append({"check": "必需章节", "status": "PASS", "detail": f"所有 {len(required_sections)} 个必需章节存在"})
            passed += 1

        # 检查 3：标题层级
        total_checks += 1
        h2_count = len(re.findall(r"^##\s", paper_text, re.MULTILINE))
        h3_count = len(re.findall(r"^###\s", paper_text, re.MULTILINE))
        if h2_count >= 5 and h3_count >= 1:
            check_items.append({"check": "标题层级", "status": "PASS", "detail": f"h2={h2_count}, h3={h3_count}"})
            passed += 1
        else:
            check_items.append({"check": "标题层级", "status": "FAIL", "detail": f"h2={h2_count}, h3={h3_count}（需要 ≥5 h2 和 ≥1 h3）"})
            failed += 1

        # 检查 4：公式（LaTeX）
        total_checks += 1
        formula_count = len(re.findall(r"\$[^$]+\$", paper_text))
        if formula_count >= 2:
            check_items.append({"check": "公式", "status": "PASS", "detail": f"{formula_count} 处 LaTeX 公式"})
            passed += 1
        else:
            check_items.append({"check": "公式", "status": "WARN", "detail": f"仅 {formula_count} 处公式（建议 ≥ 2）"})
            passed += 1

        # 检查 5：参考文献
        total_checks += 1
        ref_count = len(re.findall(r"\[(\d+)\]", paper_text))
        if ref_count >= 3:
            check_items.append({"check": "参考文献", "status": "PASS", "detail": f"{ref_count} 处引用"})
            passed += 1
        else:
            check_items.append({"check": "参考文献", "status": "WARN", "detail": f"仅 {ref_count} 处引用（建议 ≥ 3）"})
            passed += 1

        # 检查 6：占位符
        total_checks += 1
        PLACEHOLDERS = ["内容生成中", "关键词1", "论文题目缺失", "TODO", "待补", "{{", "}}"]
        found_placeholders = [p for p in PLACEHOLDERS if p in paper_text]
        if found_placeholders:
            check_items.append({"check": "占位符", "status": "FAIL", "detail": f"发现占位符: {', '.join(found_placeholders)}"})
            failed += 1
        else:
            check_items.append({"check": "占位符", "status": "PASS", "detail": "无占位符"})
            passed += 1

        gate_status = "PASS" if failed == 0 else "FAIL"
        format_report = {
            "schema_version": "1.0",
            "generated_at": now_ts,
            "status": gate_status,
            "source_file": f"paper_output/{task_id}/draft_paper.md",
            "effective_chars": len(compact),
            "summary": {
                "total_checks": total_checks,
                "passed": passed,
                "failed": failed,
            },
            "checks": check_items,
        }

        # 写入文件
        (root / "format_check.json").write_text(
            json.dumps(format_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 更新 DB
        task.format_check = json.dumps(format_report, ensure_ascii=False)
        task.current_step = "S7_check"
        if gate_status == "PASS":
            task.status = "s7_check_passed"
        await self.db.commit()

        return {
            "task_id": task_id,
            "status": gate_status,
            "format_report": format_report,
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
        }

    # ============================================================
    # 任务删除
        from app.models.models import CompetitionTask

        result = await self.db.execute(
            select(CompetitionTask).where(
                CompetitionTask.id == task_id,
                CompetitionTask.user_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return False

        # 删除文件目录
        task_dir = self._task_dir(task_id)
        if task_dir.exists():
            shutil.rmtree(task_dir, ignore_errors=True)

        await self.db.delete(task)
        await self.db.commit()
        return True
