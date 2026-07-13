# CLAUDE.md — 开发指南

> **面向对象**：Claude Code（开发助手）  
> **用途**：高效开发"AI+数学建模"双层架构平台  
> **最后更新**：2026-07-08

---

## 一、项目速览

| 项 | 值 |
|---|-----|
| 项目 | AI 数学建模智能教学平台 |
| 赛道 | 全球校园AI算法精英大赛 · AI+学科交叉 |
| 架构 | 教学平台层 (Web) + 论文引擎层 (MathModel Skill) |
| 前端 | Vue 3 + Vite + Element Plus（React 按需嵌入） |
| 后端 | Python FastAPI + SQLAlchemy + Redis |
| 引擎 | MathModel Skill v2（10 个 Claude Code Skill） |
| 部署 | Docker Compose 一键启动 |

---

## 二、快速开始

> **默认方式**：使用 Docker 一键启动前后端全部服务。

```bash
# 🐳 推荐：Docker 一键启动前后端
docker compose up -d --build

# 停止所有容器
docker compose down

# 查看服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

<details>
<summary>💻 本地开发模式（不依赖 Docker）</summary>

```bash
# 仅启动后端（开发调试）
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

# 仅启动前端（开发调试）
cd frontend && npm install && npm run dev
```

</details>

---

## 三、文档体系

```
prd/
├── AI+学科交叉-赛题规则.md          ← 比赛官方规则（只读参考）
├── tracking.md                       ← 🔴 功能追踪总表（开发唯一真相源）
├── product/                          ← 产品需求文档
│   ├── 00-数学建模-总览PRD.md
│   ├── 01-数学建模-需求分析.md
│   └── 02-数学建模-功能需求.md
├── backend/                          ← 后端开发文档
│   ├── 00-后端架构.md
│   ├── 01-API设计.md
│   ├── 02-数据模型.md
│   └── 03-AI智能体设计.md
└── frontend/                         ← 前端开发文档
    ├── 00-前端架构.md
    ├── 01-页面与路由.md
    ├── 02-组件设计.md
    └── 03-状态管理.md
```

**核心原则**：`prd/tracking.md` 是功能拆分的唯一真相源，每新增/修改功能必须同步更新。

---

## 四、功能追踪表

> **完整追踪表见 `prd/tracking.md`**，此处仅展示摘要。开发时以 `tracking.md` 为准。

### 表结构

| 列名 | 说明 |
|------|------|
| 功能ID | `MOD-XXX` 格式，模块缩写+序号 |
| 功能描述 | 一句话说清做什么 |
| 所属模块 | 学习中心/建模工作台/AI对话/竞赛训练/个人中心 |
| 优先级 | P0(首期必做) / P1(二期) / P2(三期) |
| 归属层 | 教学层 / 引擎层 / 桥接层 |
| 前端 | 未开始 / 开发中 / 已完成 |
| 后端 | 未开始 / 开发中 / 已完成 |
| Playwright测试 | 未测试 / 已通过 / 失败(附日期) |
| 用户测试 | 未测试 / 已通过 / 有问题(附反馈) |
| 后期反馈 | 上线后的用户反馈记录 |
| 备注 | 技术约束、依赖、风险 |

### 状态更新规则

- 开始开发 → 状态改为"开发中"，备注填开始日期
- 开发完成 → 状态改为"已完成"，运行 Playwright 测试
- Playwright 通过 → 标记通过日期
- 用户测试 → 记录反馈链接/截图
- 上线后反馈 → 持续追加到"后期反馈"列

---

## 五、开发命令

```bash
# === 后端 ===
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000          # 启动API服务
pytest app/tests/ -v                                # 运行后端测试

# === 前端 ===
cd frontend
npm install && npm run dev                          # 启动Vite开发服务器
npm run build                                       # 生产构建
npx playwright test                                 # 运行E2E测试

# === Docker ===
docker compose up -d --build                        # 一键启动（推荐）
docker compose down                                 # 停止所有容器
docker compose logs -f backend                      # 查看后端日志

# === MathModel Skill 参考 ===
python scripts/validate_mathmodel_skill.py           # 验证 Skill 包完整性（开发参考）
# 详细参考文档：docs/mathmodel-skill-reference.md
```

---

## 六、测试策略

| 层级 | 工具 | 覆盖范围 |
|------|------|---------|
| 后端单元测试 | pytest | API 端点、Service 层、Agent 基类 |
| 前端组件测试 | Vitest | Vue 组件、Pinia Store、Router |
| E2E 测试 | Playwright | 核心用户流程（注册→配置→对话→生成论文） |
| 引擎测试 | validate_mathmodel_skill.py | MathModel Skill 包完整性验证（10 Skill + 8 docs + Demo） |

### Playwright 测试必覆盖的流程

1. 用户注册 → 登录 → 配置 LLM API 密钥
2. 学习模式：进入知识库 → 发起 AI 对话 → 获得回复
3. 竞赛模式：上传赛题 → S0 预检 → S1 赛题分析 → 查看结果
4. 个人中心：查看历史记录 → 修改配置

### 默认测试账号

| 用户名 | 密码 | 角色 | 用途 |
|--------|------|------|------|
| `guoketg` | `123456` | admin | Playwright E2E 测试 + 开发体验 |

> 该账号在数据库首次初始化时自动创建。测试前需确保 Docker 服务已启动（`docker compose up -d --build`），且数据库卷为全新状态。

---

## 七、AI 知识嵌入位置

系统的 AI 教学能力通过后端的 Agent Prompt 文件配置，Claude Code 不需要深入理解数学建模领域知识，只需要知道：

| 知识类型 | 存储位置 | 用途 |
|---------|---------|------|
| 数学建模领域知识 | `backend/app/agents/prompts/domain_knowledge.py` | 模型分类、5步法、术语解释 |
| 教学行为准则 | `backend/app/agents/prompts/teaching_guidelines.py` | Agent 回答风格、引导策略 |
| 用户画像 | `backend/app/agents/prompts/user_profiles.py` | 3 类用户的典型场景和需求 |
| Agent 系统提示词 | `backend/app/agents/prompts/system_prompts/` | 4 个教学 Agent 的 System Prompt |

> 修改 AI 教学行为时，编辑以上文件而非 CLAUDE.md。

---

## 八、开发约定

### 🚨 第零条：tracking.md 是唯一真相源（最高优先级，不可跳过）

> **这是项目中最容易被忽略、后果最严重的规则。已在实际审查中被证实：前端 7 个页面全部完成但 tracking.md 标记全为 ⬜。**

**强制执行规则：**

| 时机 | 必须执行的操作 | 未执行的后果 |
|------|-------------|------------|
| 开始写任何代码前 | 打开 `prd/tracking.md`，找到对应功能行，确认状态为 ⬜ | 可能重复开发已完成的功能 |
| 开始写任何代码前 | 将状态改为 🟡 开发中，备注填开始日期 | tracking.md 无法反映真实进度 |
| 代码写完 + 测试通过后 | **立即**将状态改为 🟢 已完成或 ✅ 已通过 | **这是最高频的错误——代码写完就忘了更新 tracking.md** |
| 每轮对话开始 | 如果本轮要开发新功能，先读 `prd/tracking.md` 确认当前状态 | 基于过时信息做错误决策 |
| 每轮对话结束 | 回顾本轮改动的所有功能，逐行更新 tracking.md | 多次对话后 tracking.md 完全不可信 |

**自检清单（每轮对话结束时必须过一遍）：**
```
□ 本轮写了哪些功能模块？（列出功能ID）
□ 每个功能的前端/后端状态在 tracking.md 中更新了吗？
□ 每个功能的 Playwright 测试结果更新了吗？
□ 有没有新增功能需要在 tracking.md 中新建行？
```

### 开发范式（必遵守）

每完成一个功能模块，必须按以下顺序执行：

```
1. 打开 prd/tracking.md，新增/确认功能行，标记 🟡 开发中
2. 编写代码（后端 Service + Router + Schema / 前端 Vue + API）
3. 语法验证（Python ast.parse / npm run build）
4. Docker 重新构建部署（docker compose up -d --build）
5. Playwright MCP 浏览器测试（browser_navigate → snapshot → console_messages → 交互验证）
6. 检查控制台错误（0 errors 为合格）
7. 验证后端产出文件（docker exec 查看 paper_output/ 目录）
8. ⚠️ 立即更新 prd/tracking.md 对应行状态（⬜→🟢 / ⬜→✅）——不可延后！
9. 同步更新 CLAUDE.md（如有新模块/新约定/新文件结构）
```

### 核心原则

- **tracking.md 是门禁**：状态未更新 = 功能未完成，无论代码写了多少
- **功能先行**：先在 `prd/tracking.md` 新增行，再写代码
- **一次一个**：每次只做一个功能模块（如 S2），完成全流程后再做下一个
- **做完必测**：每个模块都要用 Playwright MCP 走完真实用户流程
- **门禁不可绕过**：竞赛模式的证据门禁 + 格式门禁必须 PASS
- **代码不入 skills**：赛题专用代码写 `paper_output/code/`，不写回 MathModel-Skill-master/
- **对话结束必查**：每轮对话结束时运行 tracking.md 自检清单
