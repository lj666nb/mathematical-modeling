# ============================================================
# 前端容器 Dockerfile - 多阶段构建
# 阶段1：Node环境构建Vue3项目
# 阶段2：Nginx部署静态文件
# ============================================================

# ---------- 阶段1：构建 ----------
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖配置文件
COPY package.json ./

# 安装npm依赖
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端源代码
COPY . .

# 构建生产版本
RUN npm run build

# ---------- 阶段2：部署 ----------
FROM nginx:alpine

# 复制构建产物到Nginx静态目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露80端口
EXPOSE 80

# 启动Nginx（前台运行）
CMD ["nginx", "-g", "daemon off;"]
