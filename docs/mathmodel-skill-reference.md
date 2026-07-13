# MathModel Skill 开发者参考手册

> **用途**：为前后端开发者提供 MathModel Skill 工作流引擎的核心知识，确保平台开发贴合真实数学建模痛点。
> **来源**：`MathModel-Skill-master/`（v2.0.0）
> **阅读顺序**：先读本文 → 再看具体 Skill 的 `SKILL.md` → 最后看 demo 产物

---

## 一、为什么需要这份参考？

MathModel Skill 是一个经过实战验证的数学建模论文生成工作流（Agent-native），覆盖从"读题"到"成稿"的完整 S0-S8 流水线。我们在开发教学平台时，必须理解这套引擎的：

- **工作流阶段划分**（S0-S8 每一步做什么、产出什么）
- **JSON 契约文件**（阶段间如何交接数据）
- **门禁机制**（证据门禁 + 格式门禁是如何保证论文质量的）
- **常见痛点**（长对话漂移、附件读错、代码没真跑）

> ⚠️ **关键**：MathModel Skill 是开发参考，不是给 Claude Code 执行的。引擎的工作流逻辑将在后端 `workflow_bridge/` 模块中以 API 形式重新实现。

---

## 二、S0-S8 工作流全景

```
S0: 预检 (preflight)
 │   检查 problem_files/ 文件完整性、依赖安装、output 目录布局
 │   关键脚本: preflight_check.py
 │   产出: paper_output/OUTPUT_LAYOUT.md
 │
 ▼
S1: 赛题解析 (problem-doc)
 │   读懂赛题 PDF/Word，结构化拆解为子问题、任务类型、数据附件画像
 │   关键脚本: analyze_problem.py
 │   核心契约: paper_output/step1/problem_analysis.json
 │
 ▼
S2: 模型路线 (model-route)
 │   为每个子问题推荐数学模型，对齐评分点，规划验证方案
 │   关键脚本: build_model_route.py
 │   核心契约: paper_output/plan/model_route.json, rubric_alignment.json
 │
 ▼
S3: 数据计划 (data-plan)
 │   判断附件性质（数据/参考/无用），制定数据清洗方案
 │   关键脚本: run_pipeline.py --stage data-plan
 │   核心契约: paper_output/plan/data_plan.json
 │
 ▼
S4: 数据处理 + 可视化计划 (data-code)
 │   执行数据清洗代码，制定论文图表计划
 │   关键脚本: run_pipeline.py --stage data-code
 │   核心契约: paper_output/plan/visualization_plan.json, figure_index.json
 │
 ▼
S5: 建模代码 + 结果契约 (model-code)
 │   为每问生成建模代码脚手架，运行代码，收集结果/指标/结论
 │   关键脚本: build_result_contracts.py, run_modeling.py
 │   核心契约: paper_output/results/model_results.json, metrics.json, conclusions.json
 │   产出: paper_output/code/modeling/q*_model.py
 │
 ▼
S6: 证据门禁 (evidence-gate)
 │   检查每问是否具备真实结果、图表、表格、结论——没有就退回补做
 │   关键脚本: evidence_gate.py
 │   核心契约: paper_output/qa/evidence_gate_report.json
 │   ⚠️ 这是质量底线：门禁未通过 ≠ 最终稿
 │
 ▼
S7: 正式成稿 (formal-writer)
 │   outline 规划 → Agent 全局写作 → Word 排版 → 格式门禁
 │   关键脚本: build_paper_outline.py, format_formal_docx.py, check_paper_format.py
 │   核心契约: paper_output/plan/paper_outline.json
 │   门禁: 18000-25000字 / 1→1.1→1.1.1 标题层级 / 图表引用完整性
 │   产出: paper_output/final_paper.docx
 │
 ▼
S8: 最终 QA (final-qa)
 │   全文审稿，检查逻辑连贯性、公式正确性、引用完整性
 │   关键脚本: final_qa.py
```

### 关键设计原则

| 原则 | 说明 | 对我们的启示 |
|------|------|------------|
| **防漂移** | `workflow_guard.py` 每阶段检查前置条件，防止 Agent 跳步或忘记阶段 | 后端需要 `stage_tracker` 状态机，前端需要进度可视化 |
| **契约交接** | 阶段间通过 JSON 文件传递结构化数据，不依赖"记忆" | 后端 `contract_reader` 模块需要完整支持所有 JSON schema |
| **证据门禁** | 每问必须跑出真实结果/图表/表格才能进 S7 | 前端需要展示门禁报告，不能跳过 |
| **格式门禁** | Word 必须满足字数、标题层级、引用规范 | 前端需要展示格式检查结果 |
| **代码不入 skill** | 赛题专用代码写入 `paper_output/code/`，不改动 skill 包 | 后端的代码沙箱需要写入到项目专属目录 |

---

## 三、JSON 契约文件速查

> 完整定义见 `MathModel-Skill-master/docs/workflow-contracts.md`

| 契约文件 | 生产者 | 关键字段（节选） |
|---------|--------|---------------|
| `step1/problem_analysis.json` | S1 | `sub_questions[]`, `task_types`, `data_attachments[]`, `key_concepts` |
| `plan/model_route.json` | S2 | `questions[].model`, `questions[].rationale`, `questions[].validation_plan` |
| `plan/rubric_alignment.json` | S2 | `scoring_points[].evidence_form`, `scoring_points[].related_question` |
| `plan/data_plan.json` | S3 | `data_files[].fields`, `data_files[].cleaning_tasks`, `data_files[].linked_question` |
| `plan/visualization_plan.json` | S4 | `figures[].title`, `figures[].chart_type`, `figures[].data_source` |
| `results/model_results.json` | S5 | `results[].question_id`, `results[].outputs`, `results[].parameters` |
| `results/metrics.json` | S5 | `metrics[].question_id`, `metrics[].name`, `metrics[].value` |
| `results/conclusions.json` | S5 | `conclusions[].question_id`, `conclusions[].statement` |
| `tables/table_index.json` | S5/S4 | `tables[].table_id`, `tables[].title`, `tables[].question_id`, `tables[].path` |
| `qa/evidence_gate_report.json` | S6 | `questions[].status`, `questions[].missing_evidence[]`, `questions[].score` |
| `plan/paper_outline.json` | S7 | `sections[].title`, `sections[].target_word_count`, `sections[].required_evidence` |

---

## 四、10 个 Skill 职责速查

| Skill | 阶段 | 一句话职责 |
|-------|:---:|---------|
| `paper-workflow-orchestrator` | 总控 | 入口预检 + 路由决策 + 状态管理 |
| `problem-doc-model-selector` | S1 | 赛题解析：读 PDF/Word → 结构化分析 |
| `modeling-paper-rubric-and-model-selector` | S2 | 模型选择 + 评分对齐 |
| `authoritative-data-harvester` | S3 | 获取权威公开数据 |
| `data-cleaning-and-visualization` | S3-S4 | 数据清洗 + 图表计划 + 可视化 |
| `model-code-and-result-generator` | S5 | 生成建模代码 + 运行 + 收集结果 |
| `quality-assurance-auditor` | S6 | 证据门禁检查 |
| `paper-formal-writer` | S7 | 正式论文 outline → 全局写作 → Word → 格式门禁 |
| `paper-micro-unit-generator` | S7alt | 微单元草稿生成（兜底/局部扩写） |
| `context-memory-keeper` | 全流程 | 断点记忆 + 长期准则维护 |

---

## 五、Demo 产物参考

> 完整样例见 `MathModel-Skill-master/examples/cumcm2024-b-demo/paper_output/`

| 产物 | 路径 | 用途 |
|------|------|------|
| 最终 Word 论文 | `final_paper.docx` | 可交付的正式论文 |
| Markdown 源稿 | `final_paper_source.md` | Agent 写作的正文 |
| 证据门禁报告 | `qa/evidence_gate_report.md` | 每问通过/未通过 + 缺失证据列表 |
| 格式检查报告 | `format_check_report.md` | 字数/标题/引用检查 |
| 建模代码 | `code/modeling/q*_model.py` | 每问的 Python 建模脚本 |
| 论文图表 | `figures/fig_q*_*.png` | 由实际代码生成的图表 |

---

## 六、开发时的关键注意事项

### 6.1 门禁不可绕过

竞赛模式中，证据门禁（S6）和格式门禁（S7）**必须 PASS** 才能宣称论文完成。前端 UI 必须：
- 展示门禁状态（通过/未通过/未执行）
- 未通过时显示缺失项列表
- 阻止在门禁未通过时下载"最终稿"

### 6.2 阶段依赖链

S0→S1→S2→S3→S4→S5→S6→S7→S8 是严格顺序依赖。后端 `stage_tracker` 必须：
- 验证前置阶段完成才能启动下一阶段
- 支持断点恢复（读取 `workflow_memory.json`）

### 6.3 产物目录隔离

每个竞赛项目的产物必须隔离：
```
paper_output/{project_id}/
├── step1/
├── plan/
├── code/
├── results/
├── tables/
├── figures/
├── qa/
├── context/
├── final_paper_source.md
└── final_paper.docx
```

### 6.4 长对话防漂移

MathModel Skill 的核心教训：Agent 在长对话中会"忘记"前面做了什么。对策：
- 每阶段完成后写 JSON 契约文件
- 每阶段开始前检查前置契约是否存在
- `workflow_guard.py --status` 随时可恢复当前进度

---

*本文档基于 MathModel Skill v2.0.0，随 MathModel-Skill-master/ 更新而更新。*
