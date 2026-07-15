"""
============================================================
数据验证模块 - Pydantic 请求/响应模型
应用场景：API接口数据校验，确保前后端数据格式一致
============================================================
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== 用户认证相关 ====================

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(
        ..., min_length=6, max_length=100,
        description="密码(≥6位)"
    )
    role: str = Field(default="student", description="角色: student/teacher")
    class_name: str = Field(default="", description="班级")
    display_name: str = Field(default="", description="昵称")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    role: str
    class_name: str
    display_name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class UserProfileUpdate(BaseModel):
    """更新个人资料请求"""
    display_name: str = Field(default="", max_length=100, description="显示昵称")
    class_name: str = Field(default="", max_length=100, description="班级")


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str = Field(..., min_length=6)


# ==================== LLM API配置相关 ====================

class LLMConfigCreate(BaseModel):
    """创建LLM配置请求（大赛核心创新功能）"""
    config_name: str = Field(default="默认配置", description="配置名称")
    provider: str = Field(..., description="厂商: openai/deepseek/qwen/ernie-bot")
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(default="", description="API地址")
    model_name: str = Field(default="", description="模型名称")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="最大上下文长度")


class LLMConfigUpdate(BaseModel):
    """更新LLM配置请求"""
    config_name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    is_active: Optional[int] = None


class LLMConfigInfo(BaseModel):
    """LLM配置信息响应（隐藏部分密钥）"""
    id: int
    user_id: int
    config_name: str
    provider: str
    api_key: str  # 后端返回时会脱敏
    base_url: str
    model_name: str
    temperature: float
    max_tokens: int
    is_active: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LLMTestRequest(BaseModel):
    """LLM连通性测试请求"""
    config_id: int


class LLMTestResult(BaseModel):
    """连通性测试结果"""
    success: bool
    message: str
    response_time_ms: Optional[float] = None


# ==================== 实验题库相关 ====================

class ExperimentInfo(BaseModel):
    """实验题目信息响应"""
    id: int
    subject: str
    title: str
    description: str
    reference_points: str
    difficulty: int
    template_code: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExperimentList(BaseModel):
    """实验列表响应"""
    experiments: List[ExperimentInfo]
    total: int


# ==================== 实训记录相关 ====================

class PracticeSubmit(BaseModel):
    """提交实训代码请求"""
    experiment_id: int = Field(..., description="实验ID")
    code: str = Field(..., description="提交代码")
    language: str = Field(default="python", description="编程语言")


class PracticeRecordInfo(BaseModel):
    """实训记录响应"""
    id: int
    user_id: int
    experiment_id: int
    experiment_title: Optional[str] = None
    subject: Optional[str] = None
    submitted_code: str
    language: str
    score: float
    feedback: str
    status: str
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PracticeList(BaseModel):
    """实训列表响应"""
    records: List[PracticeRecordInfo]
    total: int


# ==================== 智能体对话相关 ====================

class AgentChatRequest(BaseModel):
    """智能体对话请求"""
    agent_type: str = Field(..., description="智能体类型: code-review/training-guide/qa")
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(default=None, description="会话ID（为空则新建会话）")
    llm_config_id: Optional[int] = Field(default=None, description="使用的LLM配置ID（为空则使用默认激活配置）")
    code_context: Optional[str] = Field(default=None, description="代码上下文（代码纠错Agent使用）")


class AgentChatResponse(BaseModel):
    """智能体回复响应"""
    session_id: str
    agent_type: str
    user_message: str
    agent_message: str
    chat_id: int


class ChatHistoryInfo(BaseModel):
    """对话历史响应"""
    id: int
    agent_type: str
    session_id: str
    user_message: str
    agent_message: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatHistoryList(BaseModel):
    """对话历史列表响应"""
    sessions: List[dict]
    history: List[ChatHistoryInfo]
    total: int


class ChatRatingRequest(BaseModel):
    """Agent 回答满意度评分请求"""
    rating: int = Field(..., ge=-1, le=1, description="评分: 1=赞, -1=踩, 0=取消")


class FileUploadResponse(BaseModel):
    """聊天文件上传响应"""
    filename: str
    text_preview: str = ""
    char_count: int = 0
    session_id: str
    message: str = "上传成功"


# ==================== 教师统计相关 ====================

class TeacherStats(BaseModel):
    """教师端统计数据响应"""
    total_students: int
    total_records: int
    average_score: float
    subject_distribution: List[dict]
    score_distribution: List[dict]
    top_students: List[dict]


# ==================== 竞赛训练相关 ====================

class CompetitionTaskCreate(BaseModel):
    """创建竞赛任务请求"""
    title: str = Field(default="未命名赛题", max_length=200, description="任务名称")


class CompetitionTaskInfo(BaseModel):
    """竞赛任务信息响应"""
    id: int
    user_id: int
    title: str
    status: str
    current_step: str
    file_count: int
    preflight_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompetitionTaskDetail(BaseModel):
    """竞赛任务详情响应（含完整 S0-S7 报告数据）"""
    id: int
    user_id: int
    title: str
    status: str
    current_step: str
    file_count: int
    preflight_status: str
    preflight_report: str = ""
    input_manifest: str = ""
    problem_analysis: str = ""
    model_route: str = ""
    rubric_alignment: str = ""
    data_plan: str = ""
    visualization_plan: str = ""
    model_contract: str = ""
    evidence_gate: str = ""
    draft_paper: str = ""
    format_check: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompetitionTaskList(BaseModel):
    """竞赛任务列表响应"""
    tasks: List[CompetitionTaskInfo]
    total: int


class PreflightResult(BaseModel):
    """S0预检结果响应"""
    task_id: int
    status: str  # PASS / FAIL
    preflight_report: dict  # 完整报告
    input_manifest: dict   # 附件清单


class AnalysisResult(BaseModel):
    """S1赛题分析结果响应"""
    task_id: int
    status: str  # completed / failed
    problem_analysis: dict  # 完整分析
    questions_count: int
    task_types: List[str]


class ModelRouteResult(BaseModel):
    """S2模型路线结果响应"""
    task_id: int
    status: str  # completed / failed
    model_route: dict  # 完整模型路线
    rubric_alignment: dict  # 评分点对齐
    questions_count: int


class DataPipelineResult(BaseModel):
    """S3-S4 数据处理 + 可视化计划结果响应"""
    task_id: int
    status: str  # completed / failed
    data_plan: dict  # 数据处理计划
    visualization_plan: dict  # 可视化计划
    data_files_count: int
    figures_count: int
    charts_generated: int = 0
    chart_errors: list = []


class ModelContractResult(BaseModel):
    """S5 建模代码生成 + 结果契约响应"""
    task_id: int
    status: str  # completed / failed
    model_contract: dict  # 完整结果契约（含model_results/metrics/conclusions/table_index摘要）
    questions_count: int
    tables_count: int
    scripts_generated: int


class EvidenceGateResult(BaseModel):
    """S6 证据门禁结果响应"""
    task_id: int
    status: str  # PASS / FAIL
    gate_report: dict  # 完整门禁报告
    total_checks: int
    passed: int
    failed: int
    warnings: int


class PaperResult(BaseModel):
    """S7 论文生成结果响应"""
    task_id: int
    status: str  # completed / failed
    paper: dict  # 论文元信息（标题、摘要、章节数、字数、路径）
    sections_count: int
    word_count: int


class FormatCheckResult(BaseModel):
    """S7 格式门禁结果响应"""
    task_id: int
    status: str  # PASS / FAIL
    format_report: dict  # 完整格式检查报告
    total_checks: int
    passed: int
    failed: int
