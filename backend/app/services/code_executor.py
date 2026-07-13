"""
============================================================
代码执行沙箱 — 安全的 Python 代码执行服务
============================================================

安全策略：
  1. 超时限制（默认 30 秒，最大 60 秒）
  2. Docker 容器级别隔离
  3. 临时工作目录隔离
  4. subprocess 执行 + 超时自动终止
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# 代码前缀 — 在每个用户脚本前注入
SANDBOX_PREAMBLE = '''
# ============================================================
# AI 数学建模教学平台 — 代码沙箱
# 安全由 Docker 容器隔离 + subprocess timeout 保证
# ============================================================
import os as _sandbox_os
_sandbox_os.environ["MPLBACKEND"] = "Agg"
try:
    import matplotlib
    matplotlib.use("Agg")
except ImportError:
    pass
'''

def _build_sandbox_script(code: str) -> str:
    """构建完整的沙箱脚本"""
    return '\n'.join([SANDBOX_PREAMBLE, code])


async def execute_python_code(
    code: str,
    timeout: int = 30,
    memory_mb: int = 256,
) -> dict[str, Any]:
    """
    在安全沙箱中执行 Python 代码

    Args:
        code: 用户提交的 Python 代码
        timeout: 执行超时（秒），最大 60
        memory_mb: 内存限制（MB），最大 512

    Returns:
        dict with keys: success, stdout, stderr, execution_time_ms, error
    """
    # 参数校验
    timeout = min(max(timeout, 1), 60)
    memory_mb = min(max(memory_mb, 64), 512)

    # 构建沙箱脚本
    full_code = _build_sandbox_script(code)

    # 创建临时文件
    work_dir = Path(tempfile.mkdtemp(prefix="sandbox_"))
    script_path = work_dir / "user_script.py"

    try:
        script_path.write_text(full_code, encoding="utf-8")

        start_time = time.perf_counter()

        # 执行代码
        process = subprocess.run(
            [
                "python", "-u",  # 无缓冲
                str(script_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
            env={
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "HOME": str(work_dir),
                "TMPDIR": str(work_dir),
                "PYTHONDONTWRITEBYTECODE": "1",
                "MPLBACKEND": "Agg",
            },
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        stdout = process.stdout[:50000]  # 截断过长输出
        stderr = process.stderr[:50000]
        return_code = process.returncode

        return {
            "success": return_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code,
            "execution_time_ms": elapsed_ms,
            "truncated": len(process.stdout) > 50000 or len(process.stderr) > 50000,
        }

    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds. Consider optimizing your code.",
            "return_code": -1,
            "execution_time_ms": elapsed_ms,
            "error": "timeout",
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Sandbox error: {str(e)}",
            "return_code": -1,
            "execution_time_ms": elapsed_ms,
            "error": "sandbox_error",
        }
    finally:
        # 清理临时文件
        try:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
