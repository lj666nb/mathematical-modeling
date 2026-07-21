"""
============================================================
数据模型模块 - SQLAlchemy ORM 映射
应用场景：用户权限管理、API配置存储、实验题库、实训记录、对话历史
对应大赛评分点：完善的数据持久化方案
============================================================
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

from app.database import Base


class User(Base):
    """用户表 - 支持三级权限体系：学生/教师/管理员"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="登录账号")
    password_hash = Column(String(256), nullable=False, comment="密码哈希值")
    role = Column(String(20), nullable=False, default="student", comment="角色: student/teacher/admin")
    class_name = Column(String(100), default="", comment="班级")
    display_name = Column(String(100), default="", comment="显示昵称")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="更新时间")

    # 关联关系
    llm_configs = relationship("LLMUserConfig", back_populates="user", cascade="all, delete-orphan")
    practice_records = relationship("PracticeRecord", back_populates="user", cascade="all, delete-orphan")
    chat_records = relationship("AgentChat", back_populates="user", cascade="all, delete-orphan")
    competition_tasks = relationship("CompetitionTask", back_populates="user", cascade="all, delete-orphan")


class LLMUserConfig(Base):
    """
    用户自定义LLM API配置表（大赛核心创新功能）
    每个用户独立配置自有大模型API，服务端不内置任何密钥
    """
    __tablename__ = "llm_user_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, comment="所属用户ID")
    config_name = Column(String(100), nullable=False, default="默认配置", comment="配置名称")
    provider = Column(String(50), nullable=False, comment="厂商: openai/deepseek/qwen/ernie-bot")
    api_key = Column(Text, nullable=False, comment="API密钥")
    base_url = Column(String(500), nullable=False, default="", comment="API地址")
    model_name = Column(String(100), nullable=False, default="", comment="模型名称")
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=16384, comment="最大上下文长度")
    is_active = Column(Integer, default=1, comment="是否启用 1启用/0禁用")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="更新时间")

    # 关联用户
    user = relationship("User", back_populates="llm_configs")


class Experiment(Base):
    """
    数学建模实验题库表
    按模型分类：优化模型、预测模型、评价模型、分类与聚类、微分方程、统计模型、图论与网络、随机模型
    """
    __tablename__ = "experiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(50), nullable=False, comment="学科分类")
    title = Column(String(200), nullable=False, comment="实验题目")
    description = Column(Text, nullable=False, comment="实验要求描述")
    reference_points = Column(Text, default="[]", comment="参考知识点（JSON数组）")
    difficulty = Column(Integer, default=1, comment="难度等级 1-5")
    template_code = Column(Text, default="", comment="代码模板")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="更新时间")

    # 关联实训记录
    practice_records = relationship("PracticeRecord", back_populates="experiment")


class PracticeRecord(Base):
    """
    实训记录表
    记录学生每次实验提交的代码与AI评测结果
    """
    __tablename__ = "practice_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, comment="学生用户ID")
    experiment_id = Column(Integer, ForeignKey("experiment.id", ondelete="CASCADE"), nullable=False, comment="关联实验ID")
    submitted_code = Column(Text, nullable=False, comment="学生提交的代码")
    language = Column(String(20), default="python", comment="编程语言")
    score = Column(Float, default=0, comment="AI评分数值")
    feedback = Column(Text, default="", comment="AI评测反馈")
    status = Column(String(20), default="submitted", comment="状态: submitted/evaluated")
    completed_at = Column(DateTime, default=datetime.datetime.now, comment="完成时间")

    # 关联用户和实验
    user = relationship("User", back_populates="practice_records")
    experiment = relationship("Experiment", back_populates="practice_records")


class AgentChat(Base):
    """
    智能体对话记录表
    记录用户与AI多智能体的多轮对话，支持上下文记忆
    """
    __tablename__ = "agent_chat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    agent_type = Column(String(50), nullable=False, comment="智能体类型: code-review/training-guide/qa")
    session_id = Column(String(100), nullable=False, comment="会话ID（分组多轮对话）")
    llm_config_id = Column(Integer, ForeignKey("llm_user_config.id", ondelete="SET NULL"), nullable=True, comment="使用的API配置ID")
    user_message = Column(Text, nullable=False, comment="用户消息")
    agent_message = Column(Text, nullable=False, comment="智能体回复")
    extra_metadata = Column("metadata", Text, default="{}", comment="附加元数据JSON")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")

    # 关联
    user = relationship("User", back_populates="chat_records")


class LLMCallLog(Base):
    """
    LLM调用日志表（新增 - 借鉴自Edu-TA项目）
    记录所有LLM API调用记录，用于审计、调试和使用量统计
    每条记录包含调用的模型、耗时、Token消耗、成功/失败状态
    """
    __tablename__ = "llm_call_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, comment="用户ID")
    model = Column(String(100), default="", comment="模型名称")
    function_name = Column(String(50), default="", comment="调用功能名称")
    prompt_tokens = Column(Integer, default=0, comment="提示词Token数")
    completion_tokens = Column(Integer, default=0, comment="生成Token数")
    total_tokens = Column(Integer, default=0, comment="总Token数")
    latency_ms = Column(Integer, default=0, comment="响应延迟(毫秒)")
    success = Column(Integer, default=1, comment="是否成功 1成功/0失败")
    error_message = Column(Text, default="", comment="错误信息")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")


class CompetitionTask(Base):
    """
    竞赛任务表 — 数学建模竞赛 S0-S8 工作流追踪
    每个任务包含一个独立的 paper_output 目录，存储赛题、分析结果和论文产物
    """
    __tablename__ = "competition_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title = Column(String(200), nullable=False, default="未命名赛题", comment="任务名称")
    status = Column(String(30), nullable=False, default="created", comment="任务状态: created/files_uploaded/s0_passed/s0_failed/s1_completed/s2_completed/.../completed")
    current_step = Column(String(10), nullable=False, default="S0", comment="当前阶段: S0-S8")
    file_count = Column(Integer, default=0, comment="上传文件数量")
    preflight_status = Column(String(20), default="pending", comment="预检状态: pending/pass/fail")
    preflight_report = Column(Text, default="", comment="S0预检报告(JSON)")
    input_manifest = Column(Text, default="", comment="附件清单(JSON)")
    problem_analysis = Column(Text, default="", comment="S1赛题分析(JSON)")
    model_route = Column(Text, default="", comment="S2模型路线(JSON)")
    rubric_alignment = Column(Text, default="", comment="S2评分点对齐(JSON)")
    data_plan = Column(Text, default="", comment="S3数据处理计划(JSON)")
    visualization_plan = Column(Text, default="", comment="S4可视化计划(JSON)")
    model_contract = Column(Text, default="", comment="S5建模代码+结果契约(JSON)")
    evidence_gate = Column(Text, default="", comment="S6证据门禁报告(JSON)")
    draft_paper = Column(Text, default="", comment="S7论文草稿(JSON元信息)")
    format_check = Column(Text, default="", comment="S7格式检查报告(JSON)")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="更新时间")

    # 关联用户
    user = relationship("User", back_populates="competition_tasks")
