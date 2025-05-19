# 多阶段构建：首先使用docker.1ms.run镜像源的Python镜像作为构建环境
FROM docker.1ms.run/python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（仅构建阶段需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 升级pip并安装依赖到指定目录
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 清理不必要的文件
RUN rm -rf /root/.cache/pip \
    && rm -rf /root/.cache/matplotlib \
    && rm -rf /root/.cache/fontconfig

# 第二阶段：运行环境
FROM docker.1ms.run/python:3.12-slim

# 设置工作目录
WORKDIR /app

# 从构建器阶段复制Python依赖
COPY --from=builder /install /usr/local

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 复制应用程序代码
COPY src/ /app/src/
COPY config.yaml /app/

# 创建日志目录
RUN mkdir -p /app/logs

# 设置运行用户
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露Gradio服务的端口
EXPOSE 7860

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# 启动应用
CMD ["python", "/app/src/main.py"]
