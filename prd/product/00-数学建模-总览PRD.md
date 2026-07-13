# 00-数学建模-总览PRD

> **产品名称**：AI 数学建模智能教学平台  
> **赛道**：全球校园人工智能算法精英大赛 · 算法创新赛 · AI+学科交叉  
> **交叉学科**：数学（数学建模） × 人工智能  
> **文档版本**：v2.0  
> **创建日期**：2026-07-07  
> **更新日期**：2026-07-07（集成 MathModel Skill 工作流引擎）

---

## 一、产品愿景

### 1.1 一句话概述

打造一个 **"教学平台 + 论文引擎"双层架构**的 AI 数学建模平台——上层是 Web 交互式教学环境（AI 教数学建模），下层是 MathModel Skill 工作流引擎（Agent 生成竞赛论文），让学生既能"学会建模"又能"写出好论文"。

### 1.2 产品定位：教学平台 vs 论文引擎

本产品采用 **双层架构**，明确区分两个层次的职责：

| 层次 | 定位 | 核心能力 | 承载形式 |
|------|------|---------|---------|
| **教学平台层**（我们构建） | AI 驱动的数学建模学习环境 | 知识传授、概念讲解、互动练习、进度追踪 | Web 前端 (Vue3+React) + FastAPI 后端 |
| **论文引擎层**（集成 MathModel Skill） | Agent-native 论文生成工作流 | 赛题解析→模型路线→数据清洗→代码生成→结果证据→门禁→正式成稿 | 10 个 Claude Code Skill（S0-S8 流水线） |

**关键关系**：教学平台层负责"教"，论文引擎层负责"写"。学生在教学平台上学到建模方法和理论后，进入竞赛模式时，由 MathModel Skill 引擎驱动完整的论文生产流程。两个层次通过 JSON 契约文件（`paper_output/` 目录）进行数据交接。

### 1.3 我们要解决的问题

| 痛点 | 现状 | 本产品解决方案 |
|------|------|-------------|
| **入门门槛高** | 优化/统计/微分方程/图论等知识庞杂，学生无从下手 | 教学平台层：AI 引导式学习路径 + 结构化知识库 |
| **理论与实践脱节** | 课堂偏理论，缺乏完整流程训练 | 论文引擎层：S0-S8 流水线覆盖"读题→建模→代码→论文"全流程 |
| **反馈周期长** | 论文提交后等教师批改，无即时指导 | 双模式：学习模式即时答疑 + 竞赛模式 AI 评分/门禁检查 |
| **编程能力不足** | 非 CS 专业学生难以将模型转化为代码 | 引擎层：`model-code-and-result-generator` 自动生成代码脚手架 |
| **论文撰写困难** | 缺乏科技论文写作经验 | 引擎层：`paper-formal-writer` 提供正式论文范式 + 格式门禁 |
| **长对话上下文丢失** | Agent 对话越长越容易"忘记"前面的阶段 | 引擎层：`workflow_guard.py` + `context-memory-keeper` 防漂移 |
| **论文质量不可控** | 传统 AI 辅助容易"看起来对但实际没跑过代码" | 引擎层：证据门禁（检查真实结果/图表/表格）+ 格式门禁（18000-25000字/标题层级） |

### 1.4 产品使命

用 **AI 多智能体协同 × Agent-native 工作流引擎**，为数学建模学习者提供"学-练-赛-写"一体化智能平台。

---

## 二、双层架构总览

### 2.1 架构关系图

```
┌──────────────────────────────────────────────────────────────────────┐
│                    用户浏览器 (Web UI)                                 │
│              Vue3 SPA + React 复杂交互组件                             │
│    ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│    │ 学习中心  │ 建模工作台 │ AI对话   │ 竞赛训练  │ 个人中心  │          │
│    └──────────┴──────────┴──────────┴──────────┴──────────┘          │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ HTTP / WebSocket
┌──────────────────────────────▼───────────────────────────────────────┐
│                     FastAPI 后端 (教学平台层)                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────────┐   │
│  │ 用户系统  │ 学习管理  │ Agent服务 │ 沙箱服务  │ 工作流编排         │   │
│  │ auth     │ courses  │ teaching │ sandbox  │ workflow-orch    │   │
│  │ users    │ progress │ code_asst│ code_exec│ skill-bridge     │   │
│  │ llm_cfg  │ knowledge│ qa_agent │ viz      │ contract-sync    │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────────────┘   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              工作流桥接层 (Workflow Bridge)                      │  │
│  │  · 将 Web UI 操作翻译为 MathModel Skill 调用                      │  │
│  │  · 管理 paper_output/ 目录的 JSON 契约文件读写                    │  │
│  │  · 跟踪 S0-S8 阶段状态，同步 workflow_guard 报告                  │  │
│  │  · 调用 Claude Code Agent 执行 Skill 脚本                        │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ 文件系统 / 进程调用
┌──────────────────────────────▼───────────────────────────────────────┐
│                MathModel Skill 引擎 (论文引擎层)                       │
│                                                                       │
│  S0: preflight ──► S1: problem-doc ──► S2: model-route               │
│      预检              审题解析              模型路线                   │
│                                                                       │
│  S3: data-plan  ──► S4: data-code ──► S5: model-code                 │
│      数据计划              数据处理              建模代码                │
│                                                                       │
│  S6: evidence-gate ──► S7: formal-writer ──► S8: final-QA             │
│      证据门禁              正式成稿+格式门禁       最终审稿              │
│                                                                       │
│  10 个 Skill: orchestrator / problem-doc / model-route /              │
│  data-harvester / data-clean-viz / model-code-gen /                   │
│  qa-auditor / formal-writer / micro-unit-gen / context-memory         │
│                                                                       │
│  产物目录: paper_output/                                              │
│  ├── step1/ (problem_analysis.json + 题意对齐/大纲/评分/模型路线)       │
│  ├── plan/  (model_route / rubric / data_plan / viz_plan / outline)  │
│  ├── code/  (data_processing / visualization / modeling / qa)        │
│  ├── results/ (model_results / metrics / conclusions)                │
│  ├── tables/  (table_index.json + *.csv)                             │
│  ├── figures/ (论文图表)                                              │
│  ├── qa/      (evidence_gate_report / workflow_guard_report)          │
│  ├── context/ (workflow_memory.json)                                 │
│  ├── final_paper_source.md                                           │
│  └── final_paper.docx                                                │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 双模式设计

平台提供两种使用模式，对应不同用户场景：

| 维度 | 学习模式 | 竞赛模式 |
|------|---------|---------|
| **目标** | 掌握数学建模知识与技能 | 生成高质量竞赛论文 |
| **驱动引擎** | 教学 Agent（自研 4 大 Agent） | MathModel Skill 引擎（10 个 Skill） |
| **交互方式** | 对话式教学 + 交互式练习 + 知识库浏览 | Web UI 引导 S0-S8 分步流程 |
| **AI 角色** | 教师——讲解概念、引导思考、纠正错误 | 协作者——执行工作流、生成代码、门禁检查 |
| **产物** | 学习记录、练习代码、笔记 | `paper_output/` 完整目录 + `final_paper.docx` |
| **典型场景** | "什么是层次分析法？""帮我理解这道优化题" | "开始生成 CUMCM 2024 B 题论文" |

---

## 三、目标用户

| 用户类型 | 核心需求 | 主要模式 | 优先级 |
|---------|---------|:---:|:---:|
| **数学建模竞赛参赛者**（CUMCM/MCM/ICM等） | 赛前训练 → 竞赛时快速生成论文 | 学习模式（备赛期）+ 竞赛模式（比赛期） | P0 |
| **理工科本科生**（数学、统计、物理、工程等） | 课程学习、作业辅导、编程实践 | 学习模式 | P0 |
| **数学建模课程教师** | 教学资源管理、学生进度追踪、作业批改 | 学习模式 + 管理后台 | P1 |
| **数学建模爱好者/自学者** | 自学路径、案例库 | 学习模式 | P2 |

---

## 四、核心功能模块

### 4.1 五大模块概览

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI 数学建模智能教学平台                          │
├───────────┬───────────┬───────────┬───────────┬────────────────┤
│  学习中心  │ 建模工作台 │ AI智能体   │ 竞赛训练   │  个人中心       │
│ (教学层)   │ (教学层)   │ (教学层)   │ (引擎层)   │  (教学层)       │
├───────────┼───────────┼───────────┼───────────┼────────────────┤
│· 模型知识库│· 在线编辑器 │· 建模引导  │· 赛题管理  │· 账号管理       │
│· 方法论文献│· 数据处理  │  Agent    │· S0预检    │· LLM API密钥   │
│· 案例库   │· 可视化图表│· 代码辅助  │· S1-S8流程 │· 学习记录       │
│· 学习路径  │· 论文撰写  │  Agent    │· 证据门禁  │· 历史论文       │
│           │· 结果分析  │· 论文评审  │· 格式门禁  │· 收藏笔记       │
│           │           │  Agent    │· 最终QA    │                │
│           │           │· 数学答疑  │· Word导出  │                │
│           │           │  Agent    │           │                │
└───────────┴───────────┴───────────┴───────────┴────────────────┘
```

### 4.2 模块定位详述

| 模块 | 归属层 | 一句话定位 | 与 MathModel Skill 的关系 |
|------|:---:|----------|-------------------------|
| **学习中心** | 教学层 | 数学建模知识的结构化入口 | 独立——纯教学内容，不依赖引擎 |
| **建模工作台** | 教学层 | 从问题到论文的交互式工作环境 | 松耦合——可独立练习，也可读取引擎产物展示 |
| **AI 智能体对话** | 教学层 | 四位一体 AI 教师随时答疑 | 互补——教学 Agent 回答"为什么"，引擎 Skill 执行"怎么做" |
| **竞赛训练** | 引擎层 | S0-S8 分步流程的 Web 化操控面板 | 紧耦合——直接调用 `paper-workflow-orchestrator` 及其子 Skill |
| **个人中心** | 教学层 | 用户数据与配置管理 | 共享——LLM 密钥同时供教学 Agent 和引擎 Skill 使用 |

---

## 五、AI 智能体体系

### 5.1 双层 Agent 架构

本产品包含两类 Agent，分别服务于不同层次：

| Agent 类别 | 归属 | 数量 | 核心职责 | 运行方式 |
|-----------|------|:---:|---------|---------|
| **教学 Agent** | 教学平台层（自研） | 4 个 | 知识传授、答疑解惑、代码辅导、论文评审 | WebSocket 实时对话 |
| **工作流 Skill** | 论文引擎层（MathModel Skill） | 10 个 | 赛题解析、模型路线、数据处理、代码生成、门禁检查、正式成稿 | Claude Code Agent + Python 脚本 |

### 5.2 教学 Agent（自研 4 大 Agent）

```
                          ┌─────────────────┐
                          │  教学调度中心      │
                          │  Teaching-Dispatcher│
                          └────────┬────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
    ┌─────▼──────┐    ┌───────────▼──────┐    ┌────────────▼──────┐
    │建模引导Agent│    │ 代码辅助Agent     │    │ 论文评审Agent      │
    │            │    │                  │    │                   │
    │· 问题类型识别│    │· Python代码生成   │    │· 论文结构评审      │
    │· 模型方法推荐│    │· 算法逻辑纠错     │    │· 公式符号审查      │
    │· 建模思路引导│    │· 数值计算调试     │    │· 逻辑连贯性检查    │
    │· 假设条件分析│    │· 可视化代码辅助   │    │· 摘要质量评估      │
    │· 方法优劣对比│    │· 性能优化建议     │    │· 改进建议生成      │
    └─────┬──────┘    └───────────┬──────┘    └────────────┬──────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                         ┌─────────▼────────┐
                         │  数学答疑Agent     │
                         │                   │
                         │· 数学概念解释      │
                         │· 定理公式推导      │
                         │· 模型原理讲解      │
                         │· 算法步骤拆解      │
                         │· 文献论文解读      │
                         └───────────────────┘
```

### 5.3 工作流 Skill（MathModel Skill 引擎的 10 个 Skill）

| Skill | 阶段 | 核心功能 | 关键脚本/产物 |
|-------|:---:|---------|-------------|
| `paper-workflow-orchestrator` | S0 | 总入口：预检、路由、状态管理 | `preflight_check.py`, `workflow_guard.py`, `prepare_output_layout.py` |
| `problem-doc-model-selector` | S1 | 解析赛题 PDF/Word，结构化分析 | `analyze_problem.py` → `problem_analysis.json` |
| `modeling-paper-rubric-and-model-selector` | S2 | 模型路线选择 + 评分点对齐 | `build_model_route.py` → `model_route.json`, `rubric_alignment.json` |
| `authoritative-data-harvester` | S3 | 获取权威公开数据 | `run.py` → `crawled_data/` |
| `data-cleaning-and-visualization` | S3-S4 | 数据清洗 + 图表计划 + 可视化 | `run_pipeline.py` → `data_plan.json`, `visualization_plan.json`, `figures/` |
| `model-code-and-result-generator` | S5 | 生成建模代码脚手架 + 结果证据契约 | `build_result_contracts.py` → `q*_model.py`, `model_results.json`, `metrics.json` |
| `quality-assurance-auditor` | S6 | 证据门禁：检查每问是否具备真实结果/图表/表格/结论 | `evidence_gate.py` → `evidence_gate_report.md` |
| `paper-formal-writer` | S7 | 正式论文 outline → Agent 全局写作 → Word 排版 → 格式门禁 | `build_paper_outline.py`, `format_formal_docx.py`, `check_paper_format.py` |
| `paper-micro-unit-generator` | S7alt | 微单元草稿生成（兜底/局部扩写） | `generate_all_offline.py`, `merge.py` |
| `context-memory-keeper` | 全流程 | 断点记忆、长期准则维护 | `update_workflow_memory.py` → `workflow_memory.json` |

### 5.4 双层 Agent 协作场景

| 用户场景 | 教学 Agent 的职责 | 工作流 Skill 的职责 |
|---------|-----------------|-------------------|
| **"什么叫层次分析法？"** | 数学答疑 Agent：概念解释、步骤拆解、举例说明 | 不介入 |
| **"帮我看看这段代码哪错了"** | 代码辅助 Agent：语法检查、逻辑审查、修复建议 | 不介入 |
| **"开始生成 CUMCM 2024 B 题论文"** | 建模引导 Agent：确认选题、提示注意事项 | 全流程接管：S0 预检 → S1-S8 → 产出论文 |
| **"证据门禁没通过，帮我分析原因"** | 论文评审 Agent：解读门禁报告，给出改进方向 | qa-auditor：执行门禁检查，生成报告 |
| **"这个模型的灵敏度分析怎么做？"** | 建模引导 Agent：方法教学 → 代码辅助 Agent：生成灵敏度分析代码 | model-code-gen：补充生成灵敏度分析脚本 |

---

## 六、工作流桥接层设计

### 6.1 桥接层职责

工作流桥接层（Workflow Bridge）是教学平台层与论文引擎层之间的**翻译器**和**编排器**：

```
Web UI 用户操作
     │
     ▼
┌──────────────────────────────────────────────────────┐
│                 Workflow Bridge                       │
│                                                      │
│  1. 操作翻译：将 Web UI 按钮/表单 → Skill 调用指令      │
│  2. 契约同步：读写 paper_output/ 下的 JSON 契约文件     │
│  3. 状态追踪：解析 workflow_guard_report，展示阶段进度   │
│  4. 产物展示：将 paper_output/ 内容渲染到 Web UI        │
│  5. 错误处理：捕获 Skill 执行失败，翻译为用户可读提示     │
│                                                      │
└──────────────────────────────────────────────────────┘
     │
     ▼
MathModel Skill 引擎 (Claude Code Agent + Python 脚本)
```

### 6.2 关键接口

| Web UI 操作 | Bridge 翻译 | 对应 Skill/脚本 |
|------------|-----------|---------------|
| 上传赛题文件 | 写入 `problem_files/`，调用 `preflight_check.py` | `paper-workflow-orchestrator` (S0) |
| 点击"开始分析赛题" | 调用 `analyze_problem.py`，读取 `problem_analysis.json` | `problem-doc-model-selector` (S1) |
| 点击"生成模型路线" | 调用 `build_model_route.py`，读取 `model_route.json` | `modeling-paper-rubric-and-model-selector` (S2) |
| 点击"处理数据" | 调用 `run_pipeline.py`，展示 `data_plan.json` + 图表 | `data-cleaning-and-visualization` (S3-S4) |
| 点击"运行建模代码" | 调用 `build_result_contracts.py`，执行 `run_modeling.py` | `model-code-and-result-generator` (S5) |
| 点击"证据门禁检查" | 调用 `evidence_gate.py`，展示门禁报告 | `quality-assurance-auditor` (S6) |
| 点击"生成正式论文" | 调用 `build_paper_outline.py` → Agent 写作 → `format_formal_docx.py` | `paper-formal-writer` (S7) |
| 点击"格式检查" | 调用 `check_paper_format.py`，展示格式报告 | `paper-formal-writer` (S7) |

---

## 七、技术架构

### 7.1 技术选型

| 层级 | 技术选择 | 说明 |
|------|---------|------|
| 前端框架 | **Vue 3** + Vite + Element Plus | 主框架，页面路由、全局状态、常规 UI |
| 前端复杂交互 | **React**（按需集成） | 建模画布、交互式可视化（ECharts/D3）、代码编辑器增强（Monaco） |
| 后端框架 | **Python FastAPI** | 异步 REST API + WebSocket |
| 数据库 | SQLite / PostgreSQL | 用户数据、学习记录、项目元数据持久化 |
| 缓存会话 | Redis 7 | Agent 上下文缓存、用户会话管理 |
| LLM 网关 | 可插拔多厂商（OpenAI/DeepSeek/通义千问/GLM等） | 用户自带 API 密钥 |
| 代码沙箱 | Docker Sandbox | 隔离执行用户建模代码 |
| 论文引擎 | **MathModel Skill**（10 个 Claude Code Skill） | Agent-native 论文生成工作流 |
| 容器编排 | Docker Compose | 一键部署全部服务 |

### 7.2 部署架构

```
┌────────────────────────────────────────────────────────────┐
│                    Nginx (前端容器 :80)                      │
│        Vue3 SPA + React 组件 + 反向代理 /api → backend     │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                  FastAPI (后端容器 :8000)                    │
│  ┌─────────┬─────────┬─────────┬─────────┬──────────────┐ │
│  │ 用户模块 │ 学习模块 │ Agent对话│ 沙箱模块  │ 工作流桥接    │ │
│  │ /auth   │ /learn  │ /chat   │ /sandbox │ /workflow    │ │
│  └─────────┴─────────┴─────────┴─────────┴──────────────┘ │
│                                                            │
│  Workflow Bridge:                                          │
│  · paper_output/ 文件系统读写                               │
│  · subprocess 调用 Python 脚本                              │
│  · Claude Code Agent CLI 调用                               │
└───────────────────────────┬────────────────────────────────┘
          ┌─────────────────┼─────────────────┐
┌─────────▼──────┐  ┌───────▼───────┐  ┌──────▼──────────┐
│ Redis 容器      │  │ 数据卷          │  │ Docker Sandbox  │
│ 会话/Agent缓存  │  │ SQLite/用户文件 │  │ 代码隔离执行     │
└────────────────┘  │ paper_output/  │  └─────────────────┘
                    │ problem_files/ │
                    └────────────────┘
```

---

## 八、与大赛评分的对应关系

| 大赛评分项（分值） | 对应策略 |
|:---:|------|
| **创新性（20分）** | ① **双层架构创新**：教学 Agent + 工作流引擎的分离设计，非单一对话机器人 ② **工作流桥接层**：首次将 Agent-native Skill 工作流 Web 化 ③ **双模式切换**：学习模式与竞赛模式无缝切换 ④ 用户自定义 LLM 密钥机制 |
| **需求分析（15分）** | ① 聚焦数学建模学科 7 大痛点 ② 3 类用户画像 × 2 种使用模式精准覆盖 ③ MathModel Skill 引擎自身具备完整的需求分析能力（S1-S2） |
| **方案可行性（20分）** | ① 技术栈成熟（FastAPI + Vue3 + Docker + MathModel Skill 已验证） ② 论文引擎层已有完整 Demo（CUMCM 2024 B 题可运行样例） ③ Docker Compose 一键部署 |
| **项目实施（20分）** | ① 明确的模块划分、接口定义 ② 引擎层与教学层解耦，可独立开发测试 ③ 容器化保证环境一致性 |
| **应用效果（20分）** | ① 引擎层自带证据门禁与格式门禁，确保产出质量 ② 教学层追踪学习数据，量化效果 ③ 竞赛模式产出可直接参赛的 Word 论文 |
| **总结与展望（5分）** | ① 双层架构可复用到其他学科（物理建模、工程仿真等） ② MathModel Skill 社区已有三端支持（Claude Code/Codex/Trae） |

> 详细评分对齐分析见 `06-数学建模-评分对齐.md`

---

## 九、开发阶段规划

```
第一期 MVP（核心闭环）              第二期 能力增强               第三期 生态扩展
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│ 教学平台层：           │      │ 教学平台层：           │      │ 教学平台层：           │
│ · 用户注册/登录        │      │ · 竞赛训练 Web UI     │      │ · 社区案例分享         │
│ · LLM API 密钥配置    │      │ · 历年真题库           │      │ · 教师管理后台         │
│ · 数学答疑 Agent      │      │ · 交互式数据可视化     │      │ · 开放课题编辑器       │
│ · 建模引导 Agent      │  →   │ · React 建模画布      │  →   │ · 多学科扩展模板       │
│ · 在线代码编辑器       │      │ · 学习路径推荐         │      │                       │
│ · 模型知识库           │      │                       │      │ 引擎层：               │
│                       │      │ 引擎层：               │      │ · 社区贡献 Skill       │
│ 引擎层集成：           │      │ · 完整 S0-S8 Web 操控  │      │ · 更多竞赛格式支持     │
│ · MathModel Skill 安装 │      │ · 证据/格式门禁可视化  │      │                       │
│ · 工作流桥接层 v1      │      │ · Agent 写作过程展示   │      │                       │
│ · S1-S5 基础流程      │      │                       │      │                       │
│                       │      │                       │      │                       │
│ Docker Compose 部署    │      │                       │      │                       │
└──────────────────────┘      └──────────────────────┘      └──────────────────────┘
     ~2.5 个月                       ~2 个月                      ~2 个月
```

| 阶段 | 目标 | 核心交付物 |
|------|------|----------|
| **第一期 · MVP** | 教学平台跑通 + 引擎 S1-S5 流程可用 | 用户系统 + 2 个教学 Agent + 知识库 + 工作流桥接层 + MathModel Skill 集成 |
| **第二期 · 增强** | 完整 S0-S8 竞赛流程 Web 化 | 竞赛训练模块 + 门禁可视化 + 可视化图表 + 正式论文导出 |
| **第三期 · 生态** | 社区 + 多学科扩展 | 案例分享 + 教师端 + 开放课题 + 移动端适配 |

---

## 十、关键依赖

### 10.1 MathModel Skill 依赖

| 依赖项 | 版本/状态 | 说明 |
|------|:---:|------|
| MathModel Skill 包 | v2.0.0 | 已集成到项目中（`MathModel-Skill-master/`），需按 Claude Code 方式安装到 `.claude/skills/` |
| Python 依赖 | `requirements.txt` | pandas, numpy, matplotlib, scipy, python-docx, openpyxl, PyPDF2 等 |
| Claude Code Agent | 运行时 | 引擎层需要 Claude Code 来执行 Agent-native workflow |
| CUMCM 2024 B 题样例 | 已验证 | `examples/cumcm2024-b-demo/` 包含完整生成链路样例 |

### 10.2 现有平台复用

当前项目已有一套「AI 多智能体实训教学平台（计算机方向）」的完整代码，可复用其：
- 用户系统（注册/登录/JWT 鉴权）
- LLM API 配置管理（多厂商密钥配置）
- Docker Compose 部署方案
- Vue3 + Element Plus 前端框架

---

## 十一、参考文档

- `AI+学科交叉-赛题规则.md` — 比赛官方赛题规则与评分标准
- `01-数学建模-需求分析.md` — 详细需求分析（待创建）
- `02-数学建模-功能需求.md` — 功能需求列表（待创建）
- `03-数学建模-系统架构.md` — 详细系统架构设计（待创建）
- `04-数学建模-AI智能体设计.md` — AI Agent 详细设计（待创建）
- `05-数学建模-数据模型.md` — 数据库与 API 设计（待创建）
- `06-数学建模-评分对齐.md` — 大赛评分逐项对齐（待创建）
- `MathModel-Skill-master/README.md` — MathModel Skill 完整文档
- `MathModel-Skill-master/docs/workflow-contracts.md` — JSON 契约说明
- `MathModel-Skill-master/docs/generated-demo-workflow.md` — 正式论文生成样例
- `MathModel-Skill-master/examples/cumcm2024-b-demo/paper_output/final_paper.docx` — B 题正式 Word 样例

---

*本文档为 AI 数学建模智能教学平台的总览性 PRD v2.0，核心变更：引入 MathModel Skill 工作流引擎，形成"教学平台层 + 论文引擎层"双层架构。*
