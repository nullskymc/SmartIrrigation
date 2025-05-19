# 智能灌溉系统 Docker 部署指南

本文档提供使用 Docker 构建和运行智能灌溉系统的说明。

## 系统要求

- Docker 20.10.0 或更高版本
- Docker Compose 2.0.0 或更高版本

## 快速开始

### 1. 获取代码

```bash
git clone <仓库地址>
cd SmartIrrigation
```

或者直接一步完成：

```bash
docker-compose up --build
```

### 3. 访问系统

系统启动后，可以通过以下地址访问Web界面：

```bash
http://localhost:7860
```

## Docker配置说明

### Dockerfile

我们使用了多阶段构建来减小最终镜像的大小：

1. **构建阶段**：安装所有必要的构建依赖和Python包
2. **运行阶段**：只保留运行时必要的组件

### docker-compose.yml

通过Docker Compose配置：

- 端口映射: 7860 -> 7860
- 日志卷挂载: ./logs -> /app/logs
- 时区设置: Asia/Shanghai

## 自定义配置

### 修改端口

如需修改端口，请编辑docker-compose.yml文件：

```yaml
ports:
  - "新端口:7860"
```

### 环境变量

可以在docker-compose.yml中的environment部分添加或修改环境变量。

## 故障排除

### 问题: 无法连接到系统界面

1. 确认容器是否正常运行: `docker ps`
2. 检查日志: `docker-compose logs`
3. 检查7860端口是否被占用: `lsof -i:7860`

## 生产环境部署

对于生产环境，建议：

1. 配置SSL证书
2. 设置用户认证
3. 考虑使用外部数据库和消息队列
4. 监控系统性能和可用性
