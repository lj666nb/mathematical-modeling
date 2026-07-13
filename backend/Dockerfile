# ============================================================
# 后端容器 Dockerfile
# 应用场景：Python FastAPI 后端服务，提供RESTful API + WebSocket
# 基础镜像：python:3.11-slim（轻量级，约120MB）
# ============================================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

# 安装系统依赖（curl 用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装Python包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建运行时目录（部分为挂载点，未挂载时使用本地目录）
RUN mkdir -p /app/data /app/paper_output /app/problem_files

# 暴露API端口
EXPOSE 8000

# 启动命令：生产模式运行FastAPI应用
# 监听0.0.0.0允许容器外部访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
