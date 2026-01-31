# A2A Gateway - Self-Improvement and Deployment

**Update**: 2026-01-31 21:04:00 UTC
**Version**: 1.0.0

---

## 🎯 Self-Improvement Architecture

A2A Gateway 现在可以**使用自身来完善自己**！

### 工作流程

```
Clawdbot (或任何 Agent)
    ↓
调用 a2a-gateway
    ↓
a2a-gateway 调用外部工具（Claude Code, droid）
    ↓
外部工具执行任务
    ↓
返回结果给 a2a-gateway
    ↓
a2a-gateway 保存结果（文件、代码等）
    ↓
a2a-gateway 返回给调用者
```

### 自我完善能力

| 技能 | 描述 | 用途 |
|------|------|------|
| `fix_bug` | 修复 a2a-gateway 自身的 bug | droid 工具 |
| `refactor_code` | 重构 a2a-gateway 的代码 | Claude Code 工具 |
| `review_pr` | 审查 a2a-gateway 的 PR | Claude Code 工具 |
| `generate_dockerfile` | 生成部署文件 | Claude Code 工具（新增）|
| `generate_docker_compose` | 生成 docker-compose | Claude Code 工具（待添加）|
| `generate_k8s_manifests` | 生成 K8s manifests | Claude Code 工具（待添加）|
| `write_unit_tests` | 编写单元测试 | Claude Code 工具（待添加）|
| `improve_code_quality` | 改进代码质量 | Claude Code 工具（待添加）|

---

## 🚀 Deployment Guide

### 快速开始（开发环境）

#### 1. 使用 Docker Compose（推荐）

```bash
cd /Users/xuyangbo/github.com/a2a-gateway

# 启动所有服务（包括 Redis）
docker-compose up -d

# 查看日志
docker-compose logs -f a2a-gateway

# 停止服务
docker-compose down
```

#### 2. 使用 Docker 直接构建

```bash
cd /Users/xuyangbo/github.com/a2a-gateway

# 构建镜像
docker build -t a2a-gateway:latest .

# 运行容器
docker run -p 8000:8000 a2a-gateway:latest

# 健康检查
curl http://localhost:8000/health
```

### 生产部署

#### 1. 构建生产镜像

```bash
# 构建优化镜像
docker build -t a2a-gateway:v1.0.0 -f Dockerfile --build-arg BUILDKIT_INLINE_CACHE=1 .

# 推送到 Docker Hub
docker tag a2a-gateway:v1.0.0 xybstone/a2a-gateway:v1.0.0
docker push xybstone/a2a-gateway:v1.0.0
```

#### 2. 使用 Kubernetes（生产）

```bash
# 应用 Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 查看状态
kubectl get pods -l app=a2a-gateway
kubectl logs -f deployment/a2a-gateway
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind to |
| `PORT` | `8000` | Port to listen on |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `REDIS_ENABLED` | `false` | Enable Redis for task storage |
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `MAX_CONCURRENT_TASKS` | `5` | Maximum concurrent tasks |
| `DEFAULT_TIMEOUT` | `600` | Default task timeout in seconds |
| `DROID_COMMAND` | `droid` | Droid CLI command |
| `CLAUDE_COMMAND` | `claude` | Claude Code CLI command |

### Configuration Files

| File | Description |
|------|-------------|
| `Dockerfile` | Multi-stage Dockerfile for production builds |
| `docker-compose.yml` | Development environment orchestration |
| `.dockerignore` | Files to exclude from Docker build context |
| `pyproject.toml` | Python project configuration |
| `.env.example` | Example environment configuration |

---

## 🏗 Dockerfile Details

### Multi-Stage Build

#### Builder Stage
- **Base Image**: `python:3.11-slim`
- **Purpose**: Install build dependencies
- **Dependencies**: gcc, g++, make, libffi-dev, libssl-dev

#### Production Stage
- **Base Image**: `python:3.11-slim`
- **Purpose**: Production runtime
- **Features**:
  - Non-root user (`appuser`)
  - Optimized Python environment
  - Health check endpoint
  - Proper signal handling

### Security Features

1. **Non-Root User**
   - Creates dedicated `appuser`
   - Runs application as non-root
   - Improves security isolation

2. **Minimal Dependencies**
   - Only installs necessary runtime dependencies
   - Reduces attack surface

3. **Health Check**
   - Exposes `/health` endpoint
   - 30s interval, 10s timeout, 3 retries
   - Allows orchestration tools to monitor health

4. **Signal Handling**
   - Properly handles SIGTERM and SIGKILL
   - Graceful shutdown of gunicorn workers

---

## 📊 Service Architecture

### Components

```
┌─────────────────┐
│   Nginx (Proxy) │  ← Port 80
└─────────────────┘
        ↓
┌─────────────────┐
│  a2a-gateway  │  ← Port 8000
│  (FastAPI)       │
│  (Gunicorn)       │
└─────────────────┘
        ↓
┌─────────────────┐
│     Redis        │  ← Port 6379
│  (Optional)     │
└─────────────────┘
```

### Request Flow

```
External Request
    ↓
Nginx (Port 80)
    ↓
a2a-gateway (Port 8000)
    ↓
Tasks/Tools Execution
    ↓
External Tools (Claude Code, droid)
    ↓
Return Results
```

---

## 🎯 A2A Protocol Integration

### JSON-RPC Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent.json` | GET | A2A Agent Card |
| `/` | POST | tasks/send, tasks/get, etc. |
| `/health` | GET | Health check |

### Skill Mappings

| A2A Skill | Implementation | Tool |
|-----------|---------------|-------|
| `fix_bug` | ✅ | droid |
| `refactor_code` | ✅ | Claude Code |
| `review_pr` | ✅ | Claude Code |
| `generate_dockerfile` | ✅ | Claude Code (new) |
| `generate_docker_compose` | 🔄 | Claude Code (planned) |
| `generate_k8s_manifests` | 🔄 | Claude Code (planned) |

---

## 🔄 Continuous Improvement Loop

### Current Capabilities

```
1. ✅ Fix bugs in own codebase
2. ✅ Refactor code for better performance
3. ✅ Review pull requests
4. ✅ Generate deployment files
5. 🔄 Write unit tests (planned)
6. 🔄 Improve code quality (planned)
```

### Self-Improvement Pattern

```
Step 1: Identify need
    ↓
Step 2: Create task with skill
    ↓
Step 3: Execute task using external tool
    ↓
Step 4: Store results
    ↓
Step 5: Review and apply changes
    ↓
Step 6: Commit and push
    ↓
Back to Step 1 (continuous cycle)
```

---

## 🚀 Usage Examples

### Example 1: Fix Bug Using a2a-gateway

```json
{
  "jsonrpc": "2.0",
  "id": "fix-bug-1",
  "method": "tasks/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{
        "type": "text",
        "text": '{"bug_description": "Fix memory leak in task store", "workdir": "/Users/xuyangbo/github.com/a2a-gateway/a2a_gateway"}'
      }]
    },
    "skill": "fix_bug"
  }
}
```

### Example 2: Generate Dockerfile

```json
{
  "jsonrpc": "2.0",
  "id": "docker-gen-1",
  "method": "tasks/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{
        "type": "text",
        "text": '{"project_description": "A2A Gateway Python FastAPI application", "workdir": ".", "project_type": "python"}'
      }]
    },
    "skill": "generate_dockerfile"
  }
}
```

### Example 3: Generate docker-compose.yml

```json
{
  "jsonrpc": "2.0",
  "id": "compose-gen-1",
  "method": "tasks/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{
        "type": "text",
        "text": '{"project_description": "A2A Gateway development environment with Redis and Nginx", "workdir": ".", "project_type": "compose"}'
      }]
    },
    "skill": "generate_docker_compose"
  }
}
```

---

## 📈 Monitoring and Logging

### Health Check Endpoint

```bash
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "active_tasks": 2,
  "max_concurrent_tasks": 5,
  "uptime": "12345s"
}
```

### Logging

```python
# Structured logging configuration
logger = structlog.get_logger(__name__)

logger.info("Server started", host="0.0.0.0", port=8000)
logger.error("Task failed", task_id="task-123", error="Timeout")
logger.warning("High task load", active_tasks=5, max_concurrent_tasks=5)
```

### Metrics (Prometheus)

```
# Metrics exposed at /metrics
a2a_gateway_tasks_total
a2a_gateway_tasks_completed_total
a2a_gateway_tasks_failed_total
a2a_gateway_task_duration_seconds
a2a_gateway_active_tasks
a2a_gateway_uptime_seconds
```

---

## 🔒 Security Best Practices

### 1. Secrets Management

```bash
# Never commit secrets to version control
.env
.env.local

# Use environment variables in production
docker run -e SLACK_WEBHOOK_URL=... a2a-gateway:latest

# Use secrets orchestration
# - HashiCorp Vault
# - AWS Secrets Manager
# - Kubernetes Secrets
```

### 2. Network Security

```yaml
# Docker Compose
networks:
  a2a-gateway-network:
    driver: bridge
    internal: false

# Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: a2a-gateway-network
spec:
  podSelector:
    matchLabels:
      app: a2a-gateway
  policyTypes:
    - Ingress
```

### 3. Rate Limiting

```python
# Already implemented with SlowAPI
from slowapi import Limiter, _rate_limit_exceeded_handler

limiter = Limiter(key_func=get_remote_address)

@app.post("/")
@limiter.limit("100/minute")
async def jsonrpc_endpoint(request):
    ...
```

---

## 🐛 Troubleshooting

### Docker Issues

#### Problem: Build fails with "no space left on device"

```bash
# Solution: Clean up Docker space
docker system prune -a
docker image prune -a
docker volume prune -a
```

#### Problem: Container starts but exits immediately

```bash
# Check logs
docker logs a2a-gateway

# Check health
curl http://localhost:8000/health

# Run container interactively
docker run -it a2a-gateway:latest /bin/bash
```

### Network Issues

#### Problem: Cannot access localhost:8000

```bash
# Check if port is exposed
docker ps | grep a2a-gateway

# Check port mapping
docker port a2a-gateway 8000

# Test from inside container
docker exec a2a-gateway curl http://localhost:8000/health
```

---

## 📝 Development Workflow

### 1. Development with Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f a2a-gateway

# Restart service
docker-compose restart a2a-gateway

# Stop all services
docker-compose down
```

### 2. Development with Hot Reload

```bash
# Use mount for hot reload
docker-compose up -d

# Make changes locally
echo "test change" >> README.md

# Rebuild (optional)
docker-compose up -d --build
```

### 3. Testing

```bash
# Run tests
docker-compose exec a2a-gateway pytest

# Run specific test
docker-compose exec a2a-gateway pytest tests/test_tools.py -v

# Run with coverage
docker-compose exec a2a-gateway pytest --cov=a2a_gateway tests/ -v
```

---

## 🎯 Next Steps

### Immediate

1. ✅ **Dockerfile 已创建** - Multi-stage, production-ready
2. ✅ **docker-compose.yml 已创建** - Development environment
3. ✅ **.dockerignore 已创建** - Optimize build context
4. ✅ **generate_dockerfile 技能已实现** - Self-improvement capability

### Short-term

1. 🔄 **实现 generate_docker_compose 技能**
2. 🔄 **实现 generate_k8s_manifests 技能**
3. 🔄 **实现 write_unit_tests 技能**
4. 🔄 **添加更多测试**
5. 🔄 **改进 Prometheus 指标**

### Long-term

1. 🔄 **自动化 CI/CD pipeline**
2. 🔄 **实现自动回滚机制**
3. 🔄 **添加负载测试**
4. 🔄 **添加性能监控**
5. 🔄 **实现 A/B 测试支持**

---

## 🤖 Summary

### What We Have

✅ **A2A Gateway** - Production-ready FastAPI application
✅ **Dockerfile** - Multi-stage, optimized for production
✅ **docker-compose.yml** - Development environment
✅ **.dockerignore** - Build optimization
✅ **Self-Improvement** - Ability to use Claude Code/droid
✅ **GitHub Actions** - Automated Slack notifications

### What's Next

🔄 **DevOps Pipeline**: Code → Build → Deploy → Monitor
🔄 **Continuous Improvement**: a2a-gateway uses external tools to improve itself
🔄 **Self-Healing**: Automated bug fixing and refactoring
🔄 **Scalability**: Docker + Kubernetes support

---

**Maintainer**: 徐阳波 (xybstone)
**License**: MIT
**Repository**: https://github.com/xybstone/a2a-gateway
