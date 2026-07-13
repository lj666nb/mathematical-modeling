"""
============================================================
代码执行路由 — Python 代码沙箱执行 API
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.models.models import User
from app.routers.auth import get_current_user
from app.services.code_executor import execute_python_code


class CodeExecuteRequest(BaseModel):
    """代码执行请求"""
    code: str = Field(..., min_length=1, max_length=50000, description="Python 代码")
    timeout: int = Field(default=30, ge=1, le=60, description="超时时间（秒）")
    experiment_id: int | None = Field(default=None, description="关联的实验 ID（可选）")


class CodeExecuteResponse(BaseModel):
    """代码执行结果响应"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time_ms: int = 0
    truncated: bool = False
    error: str | None = None


router = APIRouter(prefix="/api/code", tags=["代码执行"])


@router.post("/execute", response_model=CodeExecuteResponse)
async def execute_code(
    data: CodeExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    """
    在安全沙箱中执行 Python 代码

    安全特性：
    - 超时限制（默认 30s，最大 60s）
    - 内存限制（256MB）
    - 危险模块拦截（os/sys/subprocess/socket 等）
    - 危险内置函数禁用（eval/exec/open/__import__）
    - 临时工作目录隔离
    - matplotlib 自动使用 'Agg' 非交互式后端
    """
    try:
        result = await execute_python_code(
            code=data.code,
            timeout=data.timeout,
        )
        return CodeExecuteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码执行失败：{str(e)}")
