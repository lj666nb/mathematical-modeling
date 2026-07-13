@echo off
chcp 65001 >nul
title AI多智能体实训教学平台 - 一键启动脚本 (Windows)

echo ============================================================
echo   AI多智能体 × 计算机科学与技术专业实训教学平台
echo   一键部署启动脚本 (Windows)
echo ============================================================
echo.

:: 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Docker，请先安装Docker Desktop。
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: 检查Docker Compose是否可用
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker Compose不可用，请更新Docker Desktop。
    pause
    exit /b 1
)

echo [1/4] 正在构建Docker镜像...
docker compose build
if %errorlevel% neq 0 (
    echo [错误] 镜像构建失败，请检查网络连接。
    pause
    exit /b 1
)
echo ✅ 镜像构建完成
echo.

echo [2/4] 正在启动所有容器...
docker compose up -d
if %errorlevel% neq 0 (
    echo [错误] 容器启动失败。
    pause
    exit /b 1
)
echo ✅ 容器启动完成
echo.

echo [3/4] 等待服务就绪...
timeout /t 5 /nobreak >nul
echo ✅ 服务就绪
echo.

echo [4/4] 检查运行状态...
docker compose ps
echo.

echo ============================================================
echo   🎉 部署完成！
echo.
echo   访问地址: http://localhost
echo   后端API:  http://localhost/api
echo   API文档:  http://localhost/docs (直接访问后端端口)
echo.
echo   数据存储: .\backend\data\ 目录
echo   Redis数据: Docker卷 redis_data
echo.
echo   常用命令:
echo   查看日志: docker compose logs -f
echo   停止服务: docker compose stop
echo   重启服务: docker compose restart
echo   完全停止: docker compose down
echo   重新构建: docker compose build
echo ============================================================
echo.

pause
