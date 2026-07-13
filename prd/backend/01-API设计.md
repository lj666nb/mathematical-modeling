# 01-API设计

> **文档状态**：🟢 已完成  
> **归属层**：后端开发文档  
> **前置文档**：`prd/backend/00-后端架构.md`  
> **创建日期**：2026-07-07

---

## 一、API 设计原则

| 原则 | 说明 |
|------|------|
| RESTful | 资源名词复数，HTTP 动词表达操作 |
| 统一响应 | `{code, data, message}` |
| JWT 鉴权 | `Authorization: Bearer <token>` |
| 分页 | `?page=1&page_size=20` |
| 版本 | `/api/v1/...`（首期 `/api/...`） |

### 统一响应格式

```json
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

---

## 二、API 全景路由表

### 2.1 已有路由（可复用）

| 方法 | 路径 | 说明 | 变更 |
|------|------|------|:---:|
| POST | `/api/auth/register` | 用户注册 | ✅ 复用 |
| POST | `/api/auth/login` | 用户登录 | ✅ 复用 |
| GET | `/api/auth/me` | 获取当前用户信息 | ✅ 复用 |
| PUT | `/api/auth/password` | 修改密码 | ✅ 复用 |
| POST | `/api/llm-config/create` | 创建 LLM 配置 | ✅ 复用 |
| GET | `/api/llm-config/list` | LLM 配置列表 | ✅ 复用 |
| GET | `/api/llm-config/{id}` | 获取配置详情 | ✅ 复用 |
| PUT | `/api/llm-config/{id}` | 更新配置 | ✅ 复用 |
| DELETE | `/api/llm-config/{id}` | 删除配置 | ✅ 复用 |
| POST | `/api/llm-config/test` | 连通性测试 | ✅ 复用 |
| GET | `/api/experiments/subjects` | 学科列表 | 🔧 改造 |
| GET | `/api/experiments/list` | 题库列表 | 🔧 改造 |
| POST | `/api/practice/submit` | 提交代码 | 🔧 改造 |
| POST | `/api/chat/send` | 发送消息 | 🔧 改造 |
| GET | `/api/chat/history` | 对话历史 | 🔧 改造 |
| GET | `/api/teacher/stats` | 教师统计 | ✅ 复用 |
| GET | `/api/health` | 健康检查 | ✅ 复用 |

### 2.2 新增路由

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|:---:|
| **学习中心** | | | |
| GET | `/api/learn/models` | 数学模型分类列表 | P0 |
| GET | `/api/learn/models/{id}` | 模型详情 | P0 |
| GET | `/api/learn/cases` | 案例列表 | P1 |
| GET | `/api/learn/cases/{id}` | 案例详情 | P1 |
| GET | `/api/learn/search` | 全文搜索 | P1 |
| GET | `/api/learn/path` | 学习路径推荐 | P2 |
| **建模工作台** | | | |
| POST | `/api/workspace/execute` | 代码执行（沙箱） | P0 |
| POST | `/api/workspace/upload` | 数据文件上传 | P1 |
| GET | `/api/workspace/files` | 工作区文件列表 | P1 |
| **竞赛训练** | | | |
| POST | `/api/competition/projects` | 创建竞赛项目 | P0 |
| GET | `/api/competition/projects` | 项目列表 | P0 |
| GET | `/api/competition/projects/{id}` | 项目详情 | P0 |
| POST | `/api/competition/projects/{id}/upload` | 上传赛题文件 | P0 |
| POST | `/api/competition/projects/{id}/stages/{stage}/run` | 执行某阶段 | P0 |
| GET | `/api/competition/projects/{id}/stages` | 所有阶段状态 | P0 |
| GET | `/api/competition/projects/{id}/stages/{stage}` | 某阶段详情 | P1 |
| GET | `/api/competition/projects/{id}/artifacts` | 产物文件列表 | P1 |
| GET | `/api/competition/projects/{id}/artifacts/{filename}` | 产物内容 | P1 |
| POST | `/api/competition/projects/{id}/run-auto` | 自动执行到指定阶段 | P1 |
| GET | `/api/competition/projects/{id}/export` | 导出最终论文 | P0 |
| **个人中心** | | | |
| GET | `/api/profile/history` | 学习记录 | P1 |
| GET | `/api/profile/papers` | 历史论文列表 | P1 |
| POST | `/api/profile/notes` | 添加笔记 | P2 |
| GET | `/api/profile/notes` | 笔记列表 | P2 |

---

## 三、核心 API 详细设计

### 3.1 学习中心

#### GET `/api/learn/models` — 模型分类列表

```
Query: ?category=optimization   (可选，按分类过滤)
Response:
{
  "categories": [
    { "key": "optimization", "name": "优化模型", "count": 7 },
    { "key": "prediction", "name": "预测模型", "count": 6 },
    ...
  ],
  "models": [
    {
      "id": 1,
      "category": "optimization",
      "name": "线性规划",
      "summary": "在线性约束条件下求线性目标函数的最优解",
      "difficulty": 2,
      "tags": ["单纯形法", "资源分配", "生产计划"]
    },
    ...
  ]
}
```

#### GET `/api/learn/models/{id}` — 模型详情

```
Response:
{
  "id": 1,
  "category": "optimization",
  "name": "线性规划",
  "definition": "线性规划是运筹学中...",
  "formula": "max z = c^T x, s.t. Ax ≤ b, x ≥ 0",
  "applicable_scenarios": ["资源分配", "生产计划", "运输问题"],
  "typical_methods": ["单纯形法", "对偶单纯形法", "内点法"],
  "example": {
    "problem": "某工厂生产A、B两种产品...",
    "model": "设x1为A产量, x2为B产量...",
    "solution": "最优解为 x1=20, x2=30, z=1800"
  },
  "related_models": [2, 3],
  "code_template": "from scipy.optimize import linprog\n..."
}
```

#### GET `/api/learn/search?q=层次分析法&category=all`

```
Response:
{
  "results": [
    { "type": "model", "id": 15, "title": "层次分析法 AHP", "snippet": "...", "score": 9.2 },
    { "type": "case", "id": 8, "title": "供应商选择的AHP应用", "snippet": "...", "score": 7.5 },
    ...
  ],
  "total": 12
}
```

### 3.2 建模工作台

#### POST `/api/workspace/execute` — 代码沙箱执行

```
Request:
{
  "code": "import numpy as np\n...",
  "language": "python",          // 首期仅 Python
  "timeout": 30,                 // 秒
  "files": {                     // 可选，附加数据文件
    "data.csv": "base64..."
  }
}

Response:
{
  "stdout": "最优解: x1=20.0, x2=30.0\n...",
  "stderr": "",
  "returncode": 0,
  "execution_time_ms": 1240,
  "charts": [                    // matplotlib 图表 base64
    { "format": "png", "data": "base64..." }
  ]
}
```

### 3.3 竞赛训练 — 核心流程 API

#### POST `/api/competition/projects` — 创建项目

```
Request:
{
  "title": "CUMCM 2024 B题",
  "competition": "CUMCM",
  "description": "企业生产管理中的优化问题"
}

Response:
{
  "id": "proj_abc123",
  "title": "CUMCM 2024 B题",
  "status": "created",
  "current_stage": null,
  "paper_output_dir": "/paper_output/proj_abc123/",
  "created_at": "2026-07-07T10:00:00Z"
}
```

#### POST `/api/competition/projects/{id}/upload` — 上传赛题

```
Request: multipart/form-data
  - file: <赛题PDF/Word文件>
  - attachments[]: <附件文件>

Response:
{
  "problem_file": "problem_files/proj_abc123/problem.pdf",
  "attachments": ["附件1.xlsx", "附件2.csv"],
  "file_count": 3
}
```

#### POST `/api/competition/projects/{id}/stages/{stage}/run` — 执行阶段

```
Request (可选参数):
{
  "model_override": "整数规划",    // S2可覆盖模型选择
  "params": {}                    // 阶段特定参数
}

Response (同步，脚本执行完返回):
{
  "stage": "S1",
  "status": "completed",         // completed | failed
  "output": {
    "stdout": "...",
    "stderr": ""
  },
  "contract": {                  // 从 paper_output/ 读取的契约数据
    "problem_type": "优化问题",
    "sub_questions": ["(1) 确定生产批次...", "(2) 考虑..."],
    "key_data_sources": ["附件1.xlsx"]
  },
  "elapsed_seconds": 42.5,
  "next_stage": "S2",
  "warnings": []
}
```

#### GET `/api/competition/projects/{id}/stages` — 获取所有阶段状态

```
Response:
{
  "project_id": "proj_abc123",
  "current_stage": "S2",
  "stages": {
    "S0": { "status": "completed", "started_at": "...", "elapsed": 2.1 },
    "S1": { "status": "completed", "started_at": "...", "elapsed": 42.5 },
    "S2": { "status": "running", "started_at": "...", "progress": "构建模型路线中..." },
    "S3": { "status": "pending" },
    ...
    "S8": { "status": "pending" }
  },
  "gates": {
    "evidence_gate": null,       // S6完成后才存在
    "format_gate": null          // S7完成后才存在
  }
}
```

#### POST `/api/competition/projects/{id}/run-auto` — 自动执行

```
Request:
{
  "from_stage": "S0",           // 从哪个阶段开始（默认当前）
  "until_stage": "S7",          // 执行到哪个阶段停止
  "stop_on_gate_fail": true     // 门禁失败时自动暂停
}

Response (WebSocket 流式推送进度):  // 或返回任务ID轮询
{
  "task_id": "task_xyz",
  "status": "running"
}
```

#### GET `/api/competition/projects/{id}/export` — 导出论文

```
Response: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="final_paper.docx"
```

### 3.4 Agent 对话（改造现有 chat 路由）

#### POST `/api/chat/send` — 发送消息（改造后）

```
Request:
{
  "agent_type": "math-qa",       // math-qa | modeling-guide | code-assist | paper-review
  "message": "什么是层次分析法？",
  "session_id": "sess_xxx",      // 空则新建
  "llm_config_id": 1,
  "code_context": ""             // 代码辅助 Agent 可选
}

Response:
{
  "session_id": "sess_xxx",
  "agent_type": "math-qa",
  "user_message": "什么是层次分析法？",
  "agent_message": "层次分析法（AHP）是一种...",
  "chat_id": 42,
  "suggestions": [               // 🆕 追问建议
    "AHP的判断矩阵怎么构造？",
    "一致性检验的CR值怎么算？"
  ]
}
```

#### WebSocket `/api/chat/ws?agent_type=math-qa&session_id=sess_xxx`

```
→ 用户发送: "帮我理解这道优化题"
← Agent流式回复（逐token推送）:
   { "type": "token", "content": "这" }
   { "type": "token", "content": "道" }
   ...
   { "type": "done", "chat_id": 43 }
```

### 3.5 个人中心

#### GET `/api/profile/history?page=1&page_size=20`

```
Response:
{
  "items": [
    {
      "type": "chat",            // chat | practice | competition
      "title": "与数学答疑Agent的对话",
      "summary": "讨论了层次分析法的判断矩阵构造...",
      "time": "2026-07-06T15:30:00Z",
      "link": "/agent-chat/math-qa?session=sess_xxx"
    },
    ...
  ],
  "total": 156,
  "page": 1
}
```

---

## 四、错误码定义

| HTTP Status | code | 说明 |
|:---:|------|------|
| 200 | 200 | 成功 |
| 400 | 40001 | 参数校验失败 |
| 401 | 40100 | 未认证 |
| 401 | 40101 | Token 过期 |
| 403 | 40300 | 权限不足 |
| 404 | 40400 | 资源不存在 |
| 409 | 40900 | 阶段状态冲突（如前置阶段未完成） |
| 422 | 42200 | 业务逻辑错误（如 LLM 密钥无效） |
| 500 | 50000 | 服务器内部错误 |
| 500 | 50001 | 沙箱执行失败 |
| 500 | 50002 | Skill 脚本执行失败 |

---

## 五、API 变更影响矩阵

| 变更 | 影响范围 | 影响程度 |
|------|---------|:---:|
| chat 路由 Agent 类型改为 math-qa 等 | 前端 AgentChat.vue | 中 |
| experiments 路由迁移为知识库 | 前端 Experiments.vue、后端数据库 | 中 |
| 新增 competition 路由 | 全新功能，无影响 | — |
| 新增 workspace/execute | CodeEditor.vue 需对接 | 低 |
| Agent 内部提示词全量替换 | Agent 行为变化，API 接口不变 | 低 |

---

*本文档基于现有 6 个路由模块扩展为 10 个，核心新增为竞赛训练 REST API，Agent 对话接口升级为 WebSocket 流式。*
