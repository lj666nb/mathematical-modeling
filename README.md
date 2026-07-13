# AI多智能体实训教学平台

> **全球校园人工智能算法精英大赛 · AI+学科交叉赛道**
>
> 交叉方向：AI多智能体 × 计算机科学与技术专业实训教学

---

## 一、项目概述

本平台是一款面向**计算机科学与技术专业**的AI多智能体实训教学系统，深度赋能**数据结构、操作系统、编译原理、程序设计**四大核心课程的实验/实训环节。平台采用容器化一键部署，普通学生笔记本即可运行。

### 核心创新功能

1. **自定义大模型API配置**（大赛创新点）：每个用户独立配置自有大模型API密钥，支持OpenAI/DeepSeek/通义千问/文心一言等多厂商，服务端不内置任何密钥
2. **AI多智能体协同教学**：代码纠错Agent、实训引导Agent、专业课答疑Agent三大智能体协同
3. **完整实训闭环**：在线编程 → AI评测 → 智能纠错 → 记录追踪

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户浏览器 (localhost:80)               │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│  前端容器 (Nginx)                                           │
│  · Vue3 + Element Plus 静态资源                              │
│  · 反向代理 /api → backend:8000                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ 内部网络 bridge
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐  ┌─────▼──────┐  ┌──────▼─────────┐
│  后端容器       │  │ Redis容器  │  │  数据卷          │
│  FastAPI       │  │ 会话/缓存  │  │  SQLite数据库    │
│  · 认证鉴权    │  │ Agent上下文│  │  用户配置持久化   │
│  · LLM调度     │  │  会话管理  │  │  实训记录持久化   │
│  · AI Agent    │  │           │  │                  │
└────────────────┘  └───────────┘  └──────────────────┘
```

---

## 三、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue3 + Vite + Element Plus | 组件化UI框架 |
| 后端 | Python FastAPI | 异步高性能REST API |
| 数据库 | SQLite | 轻量化文件数据库，无需额外容器 |
| 缓存 | Redis 7 | 会话管理、Agent上下文缓存 |
| 容器化 | Docker + Docker Compose | 全平台一键部署 |

---

## 四、部署步骤

### 环境要求

- **Docker**（必需）
  - Windows: Docker Desktop 4.0+
  - Linux: Docker Engine 20.0+ + Docker Compose 2.0+
  - Mac: Docker Desktop 4.0+
- **硬件最低配置**：2核CPU / 2GB内存 / 10GB磁盘

### 一键部署（Windows / Linux / Mac 通用）

```bash
# 1. 进入项目目录
cd AI-Tutoring-Platform

# 2. 构建镜像并启动所有容器
docker compose up -d --build

# 3. 查看运行状态
docker compose ps

# 4. 查看实时日志
docker compose logs -f
```

---

## 五、访问与使用

### 首次使用流程

```
1. 打开浏览器访问: http://localhost
2. 注册账号（选择学生/教师角色）
3. 登录系统
4. 进入「API配置」页面 → 添加你的LLM API密钥
5. 测试连通性验证密钥有效性
6. 开始使用AI智能体功能
```

### 核心功能页面

| 页面 | 路径 | 说明 |
|------|------|------|
| 登录注册 | /login, /register | 三级权限体系 |
| 个人看板 | /dashboard | 实训统计、快捷操作 |
| **API配置** | /llm-config | **核心创新页**，配置多厂商LLM |
| 实验题库 | /experiments | 四大课程分类题库 |
| 在线编程 | /code-editor | 代码编写、提交、AI评测 |
| AI智能体 | /agent-chat | 三大Agent对话交互 |
| 教学统计 | /teacher-stats | 教师端数据统计 |

---

## 六、支持的LLM厂商

| 厂商 | Key值 | 默认API地址 |
|------|-------|------------|
| OpenAI | openai | https://api.openai.com/v1 |
| DeepSeek | deepseek | https://api.deepseek.com/v1 |
| 通义千问 | qwen | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 文心一言 | ernie-bot | 需配置千帆平台地址 |
| 智谱GLM | glm | https://open.bigmodel.cn/api/paas/v4 |
| Moonshot | moonshot | https://api.moonshot.cn/v1 |

---

## 七、数据存储与持久化

### 数据目录

| 数据 | 存储位置 | 说明 |
|------|----------|------|
| SQLite数据库 | Docker卷 `backend_data` | 自动创建，删除容器不丢失 |
| Redis缓存 | Docker卷 `redis_data` | 会话和上下文缓存 |
| 宿主机直接访问 | `docker volume inspect` 命令查看路径 | Windows: `\\wsl$\docker\data` |

### 数据备份

```bash
# 备份SQLite数据库
docker run --rm -v backend_data:/data -v $(pwd):/backup alpine tar czf /backup/tutoring-backup.tar.gz -C /data .

# 恢复数据库
docker run --rm -v backend_data:/data -v $(pwd):/backup alpine tar xzf /backup/tutoring-backup.tar.gz -C /data
```

---

## 八、常见问题排查

### Q1: 端口80被占用
```bash
# 修改docker-compose.yml中frontend的端口映射
ports:
  - "8080:80"  # 改为8080端口
```
然后访问 http://localhost:8080

### Q2: Docker镜像构建失败
- 检查网络连接，可能需要配置镜像加速
- Windows Docker Desktop 设置 → Docker Engine → 添加 registry-mirrors

### Q3: AI智能体返回"请先配置API密钥"
- 进入「API配置」页面添加你的LLM API密钥
- 确保配置已保存并处于激活状态
- 点击「一键测试」验证连通性

### Q4: 容器启动后立即退出
```bash
# 查看详细日志
docker compose logs backend
docker compose logs redis
```

### Q5: 如何重置所有数据？
```bash
docker compose down -v    # 删除容器和数据卷
docker compose up -d      # 重新创建
```

---

## 九、维护与管理

### 常用Docker命令

```bash
# 停止服务（保留数据）
docker compose stop

# 重启服务
docker compose restart

# 完全停止并删除容器
docker compose down

# 完全停止并删除数据
docker compose down -v

# 重新构建并启动
docker compose up -d --build

# 查看各个容器资源占用
docker stats
```

---

## 十、项目目录结构

```
AI-Tutoring-Platform/
├── docker-compose.yml           # Docker编排文件
│
├── backend/                     # 后端服务
│   ├── Dockerfile               # 后端容器构建
│   ├── .dockerignore
│   ├── requirements.txt         # Python依赖
│   ├── init_db.sql              # 数据库初始化SQL
│   └── app/
│       ├── main.py              # FastAPI入口
│       ├── config.py            # 配置管理
│       ├── database.py          # 数据库引擎
│       ├── models/models.py     # ORM数据模型
│       ├── schemas/schemas.py   # Pydantic验证模型
│       ├── routers/             # API路由
│       │   ├── auth.py         # 认证接口
│       │   ├── llm_config.py   # LLM配置管理（核心）
│       │   ├── experiments.py  # 实验题库
│       │   ├── practice.py     # 实训记录
│       │   ├── chat.py         # 智能体对话
│       │   └── teacher.py      # 教师统计
│       ├── services/            # 业务服务
│       │   ├── auth_service.py # 认证服务
│       │   └── llm_service.py  # LLM调用服务
│       └── agents/             # AI多智能体（核心）
│           ├── __init__.py
│           ├── agent_base.py   # 智能体基类
│           ├── dispatcher.py   # 调度中心
│           ├── code_review_agent.py  # 代码纠错Agent
│           ├── training_guide_agent.py # 实训引导Agent
│           └── qa_agent.py     # 专业课答疑Agent
│
├── frontend/                    # 前端服务
│   ├── Dockerfile               # 前端容器构建
│   ├── .dockerignore
│   ├── nginx.conf               # Nginx反向代理配置
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/vite.svg
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js      # 路由配置
│       ├── api/index.js         # API请求封装
│       ├── stores/user.js       # Pinia状态管理
│       └── views/
│           ├── Login.vue        # 登录页
│           ├── Register.vue     # 注册页
│           ├── Dashboard.vue    # 个人看板
│           ├── LlmConfig.vue    # API配置页（核心创新）
│           ├── Experiments.vue  # 实验题库页
│           ├── CodeEditor.vue   # 在线编程页
│           ├── AgentChat.vue    # AI智能体对话页
│           └── TeacherStats.vue # 教学统计页
```

---

## 十一、大赛评分点对应

| 大赛评分点 | 对应实现 |
|------------|----------|
| 精准学科定位 | 数据结构/操作系统/编译原理/程序设计四大课程实验题库 |
| 完整可运行Web平台 | Vue3+FastAPI前后端分离，Docker一键部署 |
| 自定义大模型API | LLM配置管理页面，多厂商支持，密钥隔离存储 |
| 多智能体协同 | 调度中心 + 三大Agent（纠错/引导/答疑） |
| 容器化部署 | Docker Compose编排前端+后端+Redis三容器 |
| 数据持久化 | Docker卷挂载，删除容器不丢失数据 |
| 用户权限体系 | 学生/教师/管理员三级权限，JWT鉴权 |

---

*项目生成日期：2024年*
*大赛官网：全球校园人工智能算法精英大赛*
