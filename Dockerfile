# -------------- 构建阶段 (Builder Stage) --------------
# 使用一个轻量的 Python 镜像作为基础
FROM python:3.13.5-slim-bookworm AS builder

# 将 uv 从官方镜像中复制到我们的构建环境中
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# 设置工作目录
WORKDIR /app

# 仅复制依赖定义文件，以利用 Docker 的层缓存机制
# 只有当这些文件变化时，下面的依赖安装步骤才会重新运行
COPY pyproject.toml uv.lock ./

# 使用 uv 创建虚拟环境并安装所有依赖
RUN uv sync --frozen --no-cache

# 复制项目的全部代码到工作目录
COPY . .

# 清除构建中产生的缓存、pyc 等无用文件
RUN rm -rf ~/.cache/pip ~/.cache/uv /root/.cache \
    && find /app -type d -name '__pycache__' -exec rm -rf {} + \
    && find /app -type f -name '*.pyc' -delete

# -------------- 运行阶段 (Runner Stage) --------------
# 使用同一个轻量的 Python 镜像
FROM python:3.13.5-slim-bookworm
    
# 设置工作目录
WORKDIR /app

# 创建安全用户运行服务
RUN useradd --create-home appuser
# 将工作目录的所有权交给 appuser
RUN chown -R appuser:appuser /app

# 从 builder 拷贝已经包含代码和虚拟环境的整个 /app 目录
COPY --from=builder --chown=appuser:appuser /app /app

# 创建持久化文件夹（如上传目录，日志目录，本地sqlite数据库目录等等）
#RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# 切换到非特权用户
USER appuser

# 将虚拟环境的 bin 目录添加到 PATH 环境变量中
ENV PATH="/app/.venv/bin:$PATH"

# 暴露 FastAPI 将要使用的端口
EXPOSE 8000


# 默认启动命令（虽然在 docker-compose 中会被覆盖，但这是一个好习惯）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
