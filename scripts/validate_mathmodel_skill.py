#!/usr/bin/env python3
"""
MathModel Skill 验证脚本
检查 MathModel-Skill-master 目录结构完整性，输出关键参考信息供开发者查阅。

用途：
  - 验证 MathModel Skill 包是否完整（10 个 Skill + 关键脚本 + Demo 样例）
  - 输出 S0-S8 工作流摘要、JSON 契约列表、Demo 产物路径
  - 不安装到 .claude/skills/，仅作为开发参考验证

用法：
  python scripts/validate_mathmodel_skill.py
  python scripts/validate_mathmodel_skill.py --json   # JSON 格式输出
"""

import os
import sys
import json
from pathlib import Path

# Windows 终端 UTF-8 支持
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = PROJECT_ROOT / "MathModel-Skill-master"
SKILLS_DIR = SKILL_ROOT / "packages" / "claude" / ".claude" / "skills"

# 期望的 10 个 Skill 目录
EXPECTED_SKILLS = [
    "paper-workflow-orchestrator",
    "problem-doc-model-selector",
    "modeling-paper-rubric-and-model-selector",
    "authoritative-data-harvester",
    "data-cleaning-and-visualization",
    "model-code-and-result-generator",
    "quality-assurance-auditor",
    "paper-formal-writer",
    "paper-micro-unit-generator",
    "context-memory-keeper",
]

# 关键文档
KEY_DOCS = [
    "README.md",
    "GETTING_STARTED.md",
    "requirements.txt",
    "docs/workflow-contracts.md",
    "docs/output-layout.md",
    "docs/generated-demo-workflow.md",
    "docs/cumcm-paper-standard.md",
    "docs/formal-paper-authoring.md",
]

# Demo 关键产物
DEMO_ARTIFACTS = [
    "examples/cumcm2024-b-demo/paper_output/final_paper.docx",
    "examples/cumcm2024-b-demo/paper_output/qa/evidence_gate_report.md",
    "examples/cumcm2024-b-demo/paper_output/step1/problem_analysis.json",
    "examples/cumcm2024-b-demo/paper_output/plan/model_route.json",
    "examples/cumcm2024-b-demo/paper_output/code/modeling/run_modeling.py",
]


def check_skill_root() -> dict:
    """检查 MathModel-Skill-master 目录是否存在"""
    exists = SKILL_ROOT.exists()
    return {
        "status": "ok" if exists else "missing",
        "path": str(SKILL_ROOT),
        "message": "✅ MathModel-Skill-master 目录存在" if exists
                    else "❌ MathModel-Skill-master 目录不存在！请确认已克隆或解压 MathModel Skill 包"
    }


def check_skills() -> list[dict]:
    """检查 10 个 Skill 目录是否完整"""
    results = []
    for skill_name in EXPECTED_SKILLS:
        skill_dir = SKILLS_DIR / skill_name
        has_skill_md = (skill_dir / "SKILL.md").exists()
        has_scripts = (skill_dir / "scripts").exists()
        results.append({
            "name": skill_name,
            "path": str(skill_dir),
            "exists": skill_dir.exists(),
            "has_skill_md": has_skill_md,
            "has_scripts": has_scripts,
        })
    return results


def check_key_docs() -> list[dict]:
    """检查关键文档"""
    results = []
    for doc_path in KEY_DOCS:
        full_path = SKILL_ROOT / doc_path
        results.append({
            "path": doc_path,
            "exists": full_path.exists(),
        })
    return results


def check_demo_artifacts() -> list[dict]:
    """检查 Demo 产物"""
    results = []
    for artifact_path in DEMO_ARTIFACTS:
        full_path = SKILL_ROOT / artifact_path
        results.append({
            "path": artifact_path,
            "exists": full_path.exists(),
        })
    return results


def print_summary():
    """打印 S0-S8 工作流摘要"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        MathModel Skill — S0-S8 工作流摘要                    ║
╠══════════════════════════════════════════════════════════════╣
║  S0  预检        preflight_check.py                         ║
║  S1  赛题解析    analyze_problem.py → problem_analysis.json  ║
║  S2  模型路线    build_model_route.py → model_route.json     ║
║  S3  数据计划    run_pipeline.py → data_plan.json            ║
║  S4  数据处理    run_pipeline.py → visualization_plan.json   ║
║  S5  建模代码    build_result_contracts.py → results/        ║
║  S6  证据门禁    evidence_gate.py → evidence_gate_report     ║
║  S7  正式成稿    build_paper_outline → format → check        ║
║  S8  最终 QA     final_qa.py                                ║
╠══════════════════════════════════════════════════════════════╣
║  📄 开发者参考: docs/mathmodel-skill-reference.md            ║
║  📦 Demo 样例:  examples/cumcm2024-b-demo/paper_output/     ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    output_json = "--json" in sys.argv

    if not output_json:
        print("=" * 60)
        print("  MathModel Skill 验证工具")
        print("  用途：验证 Skill 包完整性（开发参考，非安装脚本）")
        print("=" * 60)

    # 1. 检查根目录
    root_check = check_skill_root()

    # 2. 检查 Skill 目录
    skills_check = check_skills()

    # 3. 检查关键文档
    docs_check = check_key_docs()

    # 4. 检查 Demo 产物
    artifacts_check = check_demo_artifacts()

    # 统计
    skills_ok = sum(1 for s in skills_check if s["exists"])
    skills_with_md = sum(1 for s in skills_check if s["has_skill_md"])
    docs_ok = sum(1 for d in docs_check if d["exists"])
    artifacts_ok = sum(1 for a in artifacts_check if a["exists"])

    if output_json:
        result = {
            "root": root_check,
            "skills": {
                "total": len(skills_check),
                "present": skills_ok,
                "with_skill_md": skills_with_md,
                "details": skills_check,
            },
            "docs": {
                "total": len(docs_check),
                "present": docs_ok,
                "details": docs_check,
            },
            "demo_artifacts": {
                "total": len(artifacts_check),
                "present": artifacts_ok,
                "details": artifacts_check,
            },
            "summary": f"Skills: {skills_ok}/{len(EXPECTED_SKILLS)} | Docs: {docs_ok}/{len(KEY_DOCS)} | Demo: {artifacts_ok}/{len(DEMO_ARTIFACTS)}"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 文字输出
    print(f"\n📁 根目录: {root_check['message']}")

    print(f"\n📦 Skill 目录 ({skills_ok}/{len(EXPECTED_SKILLS)} 存在):")
    for s in skills_check:
        icon = "✅" if s["exists"] and s["has_skill_md"] else "⚠️" if s["exists"] else "❌"
        print(f"  {icon} {s['name']}")

    print(f"\n📄 关键文档 ({docs_ok}/{len(KEY_DOCS)} 存在):")
    for d in docs_check:
        icon = "✅" if d["exists"] else "❌"
        print(f"  {icon} {d['path']}")

    print(f"\n📊 Demo 产物 ({artifacts_ok}/{len(DEMO_ARTIFACTS)} 存在):")
    for a in artifacts_check:
        icon = "✅" if a["exists"] else "❌"
        print(f"  {icon} {a['path']}")

    print_summary()

    if root_check["status"] != "ok":
        print("❌ 致命错误：MathModel-Skill-master 目录缺失！")
        print("   请从以下来源获取：")
        print("   - 项目仓库中应包含 MathModel-Skill-master/ 子目录")
        sys.exit(1)

    if skills_ok < 8:
        print("⚠️  警告：部分 Skill 缺失，可能影响开发参考完整性")
        sys.exit(1)

    print("✅ MathModel Skill 验证通过 — 开发者可参考 docs/mathmodel-skill-reference.md")


if __name__ == "__main__":
    main()
