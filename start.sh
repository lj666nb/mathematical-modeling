#!/bin/bash
# ============================================================
# AI多智能体 × 计算机科学与技术专业实训教学平台
# 一键部署启动脚本 (Linux/Mac)
# ============================================================

set -e

echo "============================================================"
echo "  AI多智能体 × 计算机科学与技术专业实训教学平台"
echo "  一键部署启动脚本 (Linux/Mac)"
echo "============================================================"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "[错误] 未检测到Docker，请先安装Docker。"
    echo "安装指南: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查Docker Compose是否可用
if ! docker compose version &> /dev/null; then
    echo "[错误] Docker Compose不可用，请更新Docker。"
    exit 1
fi

echo "[1/4] 正在构建Docker镜像..."
docker compose build
echo "✅ 镜像构建完成"
echo ""

echo "[2/4] 正在启动所有容器..."
docker compose up -d
echo "✅ 容器启动完成"
echo ""

echo "[3/4] 等待服务就绪..."
sleep 5
echo "✅ 服务就绪"
echo ""

echo "[4/4] 检查运行状态..."
docker compose ps
echo ""

echo "============================================================"
echo "  🎉 部署完成！"
echo ""
echo "  访问地址: http://localhost"
echo "  后端API:  http://localhost/api"
echo "  API文档:  http://localhost:8000/docs"
echo ""
echo "  数据存储: ./backend/data/ 目录"
echo "  Redis数据: Docker卷 redis_data"
echo ""
echo "  常用命令:"
echo "  查看日志: docker compose logs -f"
echo "  停止服务: docker compose stop"
echo "  重启服务: docker compose restart"
echo "  完全停止: docker compose down"
echo "  重新构建: docker compose build"
echo "============================================================"
