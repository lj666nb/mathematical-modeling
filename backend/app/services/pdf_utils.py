"""
============================================================
PDF 文本提取工具 — 多引擎降级
应用场景：聊天文件上传、竞赛模块 PDF 解析
引擎链：PyMuPDF (fitz) → pypdf → 返回空字符串
============================================================
"""
from importlib import import_module
from pathlib import Path
from typing import Union


def safe_import(name: str):
    """安全导入可选依赖，模块缺失返回 None"""
    try:
        return import_module(name)
    except Exception:
        return None


def extract_pdf_text(file_path: Union[str, Path]) -> str:
    """
    从 PDF 文件提取全文，多引擎自动降级

    Args:
        file_path: PDF 文件路径（str 或 Path 对象）

    Returns:
        提取的文本内容，所有引擎失败时返回空字符串 ""
    """
    path = Path(file_path)

    # 引擎 1：PyMuPDF（首选，质量最高）
    fitz = safe_import("fitz")
    if fitz:
        try:
            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            if text.strip():
                return text
        except Exception:
            pass

    # 引擎 2：pypdf
    pypdf = safe_import("pypdf")
    if pypdf:
        try:
            reader = pypdf.PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass

    return ""
