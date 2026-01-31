# A2A 编码网关产品需求文档 (PRD) v2.0

**项目名称:** A2A Coding Gateway for Clawdbot
**版本:** v1.0
**创建日期:** 2026-01-31
**更新日期:** 2026-01-31
**作者:** 三弟 (产品经理 & 技术架构师)
**状态:** 待评审

---

## 📋 执行摘要

### 项目背景

Clawdbot 作为 AI 助手，需要调用编码工具（droid、Claude Code）来完成代码相关任务。当前通过终端直接调用这些工具存在以下问题：

1. **交互复杂**: 编码工具需要多轮对话，直接调用难以管理
2. **PTY 兼容性**: 编码工具需要伪终端（PTY），调用方式特殊
3. **状态管理**: 长时间任务需要跟踪进度和状态
4. **协议标准**: 缺乏标准化的 Agent 通信协议

### 解决方案

构建一个轻量级 A2A（Agent-to-Agent）网关，将 Clawdbot 与编码工具通过标准 A2A 协议连接：

- **无需 Temporal**: 简化架构，直接使用 FastAPI + subprocess
- **标准 A2A 协议**: 兼容 Agent Card、JSON-RPC 2.0
- **PTY 支持**: 正确处理编码工具的终端交互
- **任务管理**: 支持任务生命周期（submitted → working → completed/failed）
- **数据持久化**: 可选 Redis 支持，避免任务丢失

### 核心价值

| 指标 | 当前状态 | 目标状态 |
|------|---------|---------|
| Agent 通信标准 | 无标准化 | A2A 标准协议 |
| 编码工具集成 | 手动终端调用 | 自动化网关 |
| 任务可追踪性 | 无 | 完整生命周期 |
| 数据持久化 | 无 | 可选 Redis |
| 系统复杂度 | N/A | 最小化（无 Temporal） |

---

## 🎯 产品目标

### 主要目标

1. **标准化通信**: 实现 A2A 协议，使 Clawdbot 能以标准方式调用编码 Agent
2. **简化集成**: 无需 Temporal，降低运维和学习成本
3. **可靠执行**: 正确处理 PTY 交互，确保编码工具稳定运行
4. **可观测性**: 提供任务状态查询、日志记录、错误追踪
5. **生产级运维**: 完整的部署、监控、告警、发布流程

### 成功指标

- ✅ Clawdbot 通过 A2A 协议成功调用编码工具
- ✅ 支持至少 2 种编码工具（droid、Claude Code）
- ✅ 任务成功率 > 95%
- ✅ 平均响应时间 < 30 秒（简单任务）
- ✅ 支持 5 个并发任务
- ✅ 数据持久化（可选 Redis）
- ✅ 完整监控和告警
- ✅ 自动化部署流程

---

## 🔧 功能需求

### FR1: A2A 协议支持

#### FR1.1 Agent Card
网关必须通过 `/.well-known/agent.json` 暴露 Agent Card：

```json
{
  "name": "ClawdbotCodingAgent",
  "description": "Fixes bugs, refactors code, and reviews PRs",
  "url": "http://localhost:8000",
  "interfaces": [{"url": "http://localhost:8000", "transport": "JSONRPC"}],
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "fix_bug",
      "name": "Fix Bug",
      "description": "Fix a bug in codebase",
      "inputSchema": {
        "type": "object",
        "properties": {
          "bug_description": {"type": "string"},
          "workdir": {"type": "string"},
          "context_files": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["bug_description"]
      }
    }
  ]
}
```

#### FR1.2 JSON-RPC 2.0 端点
网关必须实现以下端点：

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/` | JSON-RPC 2.0 主端点（处理 `tasks/send`, `tasks/get` 等）|
| GET | `/.well-known/agent.json` | 返回 Agent Card |
| GET | `/health` | 健康检查 |
| GET | `/metrics` | Prometheus 指标 |

**JSON-RPC 方法:**

- `tasks/send`: 创建新任务
  ```json
  {
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "id": "client-id",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "{\"bug_description\": \"...\"}"}]
      },
      "skill": "fix_bug"
    }
  }
  ```

- `tasks/get`: 查询任务状态
  ```json
  {
    "jsonrpc": "2.0",
    "method": "tasks/get",
    "id": "client-id",
    "params": {"id": "task-id"}
  }
  ```

#### FR1.3 任务生命周期
任务状态必须支持：

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `submitted` | 任务已接收，未开始 | `tasks/send` 成功 |
| `working` | 任务执行中 | 编码工具启动 |
| `completed` | 任务成功完成 | 编码工具返回结果 |
| `failed` | 任务失败 | 编码工具出错或超时 |
| `canceled` | 任务被取消 | 用户取消任务 |

### FR2: 编码工具集成

#### FR2.1 droid 集成
- 支持通过 subprocess 调用 droid
- 使用 PTY 模式启动（确保终端兼容）
- 支持传递工作目录参数
- 支持传递任务描述和上下文

#### FR2.2 Claude Code 集成
- 支持通过 subprocess 调用 Claude Code
- 使用 PTY 模式启动
- 支持多轮对话交互
- 支持传递项目上下文

#### FR2.3 工具切换
- 根据 `skill_id` 自动选择工具
- 支持动态添加新编码工具
- 配置文件管理工具参数

### FR3: PTY 终端处理

#### FR3.1 PTY 启动
- 所有编码工具必须通过 PTY 启动
- 正确处理终端输出（ANSI 转义码）
- 支持超时机制

#### FR3.2 输出解析
- 提取编码工具的有效输出
- 过滤终端控制字符
- 保留错误信息用于调试

#### FR3.3 交互式输入
- 支持向编码工具发送输入（如确认 "yes"）
- 处理多轮对话场景
- 支持超时自动取消

### FR4: 任务管理

#### FR4.1 任务存储
- 默认内存存储（InMemoryTaskStore）
- 可选 Redis 持久化
- 支持并发任务
- 任务 ID 使用 UUID

#### FR4.2 并发控制
- 支持最多 5 个并发任务
- 超出限制时返回错误
- 可配置并发数量

#### FR4.3 超时处理
- 默认超时 10 分钟
- 可通过参数调整
- 超时后任务状态变为 `failed`

### FR5: 数据持久化

#### FR5.1 Redis 集成
- 可选的 Redis 后端用于任务持久化
- 支持任务状态保存到 Redis
- 服务重启后恢复未完成任务
- 配置开关控制是否启用

#### FR5.2 数据模型
```python
# Redis Key 格式
task:{task_id} → Task 对象（JSON 序列化）
tasks:pending → ZSET（按创建时间排序）
tasks:working → ZSET
tasks:completed → ZSET
tasks:failed → ZSET
```

#### FR5.3 数据清理
- 完成的任务保留 24 小时
- 失败的任务保留 7 天
- 自动清理过期数据
- 可配置保留时间

### FR6: 错误处理

#### FR6.1 错误日志
- 记录所有任务错误
- 包含任务 ID、错误类型、堆栈信息
- 日志级别：ERROR
- 错误日志持久化到 Redis

#### FR6.2 错误返回
- JSON-RPC 错误格式
- 包含错误代码和消息
- 区分业务错误和系统错误

#### FR6.3 重试机制
- 可选的任务重试
- 最多重试 3 次
- 指数退避策略

### FR7: 可观测性

#### FR7.1 健康检查
- `/health` 端点
- 返回服务状态和版本信息
- 检查 Redis 连接（如果启用）

#### FR7.2 任务查询
- 支持通过 `tasks/get` 查询任务状态
- 返回完整任务信息（状态、进度、结果）
- 支持批量查询

#### FR7.3 日志记录
- 结构化日志（JSON 格式）
- 包含时间戳、级别、消息、上下文
- 日志级别可配置
- 日志输出到 stdout + 文件

#### FR7.4 Prometheus 指标
- `/metrics` 端点暴露 Prometheus 格式指标
- 关键指标：
  - `a2a_gateway_tasks_total{status}`: 任务总数（按状态）
  - `a2a_gateway_task_duration_seconds`: 任务执行时间
  - `a2a_gateway_active_tasks`: 当前活跃任务数
  - `a2a_gateway_http_requests_total{method, status}`: HTTP 请求数
  - `a2a_gateway_tool_invocations_total{tool, skill}`: 工具调用次数
  - `a2a_gateway_redis_health`: Redis 健康状态（0/1）

---

## 🏗️ 技术架构

### 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Clawdbot (调用者)                          │
│                                                               │
│  发送 A2A 任务请求 (JSON-RPC 2.0)                              │
└─────────────────────────────────────────────────────────────┘
                          │ HTTPS / HTTP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              A2A Gateway (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Agent Card Service                                  │   │
│  │  • GET /.well-known/agent.json                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  JSON-RPC Handler                                   │   │
│  │  • tasks/send → TaskScheduler                      │   │
│  │  • tasks/get → TaskStore                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Task Scheduler                                     │   │
│  │  • 创建任务 → TaskStore                             │   │
│  │  • 分配 Worker → CodingAgentExecutor                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Task Store (InMemory / Redis)                      │   │
│  │  • 存储任务状态                                    │   │
│  │  • 支持 CRUD 操作                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          CodingAgentExecutor (异步任务执行)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PTY Process Manager                                │   │
│  │  • 启动编码工具 (pty.spawn)                        │   │
│  │  • 管理进程生命周期                                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Output Parser                                      │   │
│  │  • 解析终端输出                                    │   │
│  │  • 提取有效内容                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Result Collector                                   │   │
│  │  • 收集任务结果                                    │   │
│  │  • 更新任务状态                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │ PTY
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         编码工具 (droid / Claude Code)                      │
│  • 运行在 PTY 中                                             │
│  • 输出重定向到 Gateway                                     │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术 | 版本 | 理由 |
|------|------|------|------|
| HTTP 框架 | FastAPI | 0.104+ | 高性能、异步、自动文档 |
| A2A SDK | a2a-sdk | 0.1+ | 官方 A2A 协议实现 |
| 进程管理 | ptyprocess | 0.7+ | PTY 终端处理 |
| 异步运行时 | asyncio | Python 3.11+ | 标准异步库 |
| 数据验证 | Pydantic | 2.0+ | 请求/响应验证 |
| 日志 | structlog | 23.0+ | 结构化日志 |
| 指标 | prometheus-client | 0.19+ | Prometheus 指标暴露 |
| 数据持久化 | redis-py | 5.0+ | Redis 客户端（可选） |
| 配置管理 | pydantic-settings | 2.0+ | 环境变量配置 |

### 组件职责

#### A2AFastAPIApplication
- 实现 A2A 协议端点
- 路由 JSON-RPC 请求到处理器
- 返回标准 JSON-RPC 响应

#### DefaultRequestHandler
- 解析 JSON-RPC 请求
- 验证请求参数
- 调用相应的 AgentExecutor

#### AgentExecutor (CodingAgentExecutor)
- 执行任务逻辑
- 管理任务生命周期
- 调用编码工具

#### TaskStore (InMemoryTaskStore / RedisTaskStore)
- 存储任务状态
- 提供 CRUD 操作
- 支持并发访问
- 可选 Redis 持久化

#### PTYProcessManager
- 启动 PTY 进程
- 管理输入/输出
- 处理超时

#### MetricsCollector
- 收集 Prometheus 指标
- 暴露 `/metrics` 端点

---

## 🚀 部署和运维

### 环境要求

#### 最小配置
- CPU: 2 核
- 内存: 2 GB
- 磁盘: 10 GB
- Python: 3.11+
- Redis: 可选（如需持久化）

#### 推荐配置
- CPU: 4 核
- 内存: 4 GB
- 磁盘: 50 GB
- Redis: 单机实例

### 部署方式

#### 方式 1: Docker 容器部署

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "a2a_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - MAX_CONCURRENT_TASKS=5
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis_data:
  grafana_data:
```

**启动:**
```bash
docker-compose up -d
```

#### 方式 2: Kubernetes 部署

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-gateway
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: a2a-gateway
  template:
    metadata:
      labels:
        app: a2a-gateway
    spec:
      containers:
      - name: gateway
        image: a2a-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: a2a-gateway-config
              key: redis_url
        - name: LOG_LEVEL
          value: "INFO"
        - name: MAX_CONCURRENT_TASKS
          value: "5"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: a2a-gateway-service
  namespace: default
spec:
  selector:
    app: a2a-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**部署:**
```bash
kubectl apply -f deployment.yaml
```

#### 方式 3: Systemd 服务（Linux）

**/etc/systemd/system/a2a-gateway.service:**
```ini
[Unit]
Description=A2A Coding Gateway
After=network.target

[Service]
Type=simple
User=a2a
WorkingDirectory=/opt/a2a-gateway
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="LOG_LEVEL=INFO"
ExecStart=/opt/a2a-gateway/.venv/bin/uvicorn a2a_gateway.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable a2a-gateway
sudo systemctl start a2a-gateway
```

### 配置管理

#### 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `GATEWAY_HOST` | `0.0.0.0` | 绑定地址 |
| `GATEWAY_PORT` | `8000` | 绑定端口 |
| `REDIS_URL` | `None` | Redis 连接 URL（可选） |
| `LOG_LEVEL` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `MAX_CONCURRENT_TASKS` | `5` | 最大并发任务数 |
| `DEFAULT_TIMEOUT` | `600` | 默认超时（秒） |
| `TASK_RETENTION_DAYS` | `7` | 任务保留天数 |
| `METRICS_ENABLED` | `true` | 是否启用指标 |
| `API_KEY` | `None` | API Key（可选认证） |

#### config.yaml
```yaml
gateway:
  host: "0.0.0.0"
  port: 8000
  max_concurrent_tasks: 5
  default_timeout: 600  # 10 minutes

redis:
  url: "redis://localhost:6379/0"
  enabled: true
  task_retention_days: 7

tools:
  droid:
    command: "droid"
    use_pty: true
    timeout: 600

  claude:
    command: "claude"
    use_pty: true
    timeout: 600

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/a2a-gateway/gateway.log"

monitoring:
  metrics_enabled: true
  metrics_port: 8000

security:
  api_key: ${API_KEY}  # 从环境变量读取
  cors_origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
```

### 运维指南

#### 健康检查
```bash
# 基本健康检查
curl http://localhost:8000/health

# 详细健康检查（包括 Redis）
curl http://localhost:8000/health?detailed=true
```

#### 日志查看
```bash
# Docker
docker-compose logs -f gateway

# Kubernetes
kubectl logs -f deployment/a2a-gateway

# Systemd
sudo journalctl -u a2a-gateway -f

# 日志文件
tail -f /var/log/a2a-gateway/gateway.log
```

#### 重启服务
```bash
# Docker
docker-compose restart gateway

# Kubernetes
kubectl rollout restart deployment/a2a-gateway

# Systemd
sudo systemctl restart a2a-gateway
```

#### 性能监控
```bash
# 查看 Prometheus 指标
curl http://localhost:8000/metrics

# 查看当前活跃任务
curl http://localhost:8000/metrics | grep a2a_gateway_active_tasks

# 查看任务成功率
curl http://localhost:8000/metrics | grep a2a_gateway_tasks_total
```

#### 数据清理
```bash
# 手动清理 Redis 中的过期任务
redis-cli --scan --pattern "task:*" | xargs -L 1000 redis-cli DEL

# 清理特定状态的任务
redis-cli --scan --pattern "tasks:failed:*" | xargs -L 1000 redis-cli DEL
```

---

## 🔐 安全设计

### API Key 管理

#### 配置方式
```yaml
# 从环境变量读取
security:
  api_key: ${A2A_API_KEY}
```

```bash
# 设置环境变量
export A2A_API_KEY=your-secret-key-here
```

#### 使用方式
```bash
# 客户端请求时携带 API Key
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key-here" \
  -d '{"jsonrpc": "2.0", "method": "tasks/send", ...}'
```

### 输入验证

#### 参数验证
- 所有 JSON-RPC 请求参数必须通过 Pydantic 验证
- 防止 SQL 注入、命令注入
- 过滤敏感信息（密码、API Key）

```python
from pydantic import BaseModel, validator

class FixBugRequest(BaseModel):
    bug_description: str
    workdir: str = "."
    context_files: list[str] = []

    @validator('workdir')
    def validate_workdir(cls, v):
        # 防止路径遍历攻击
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid workdir')
        return v
```

### 日志脱敏

#### 敏感信息过滤
```python
import re

def sanitize_log(message: str) -> str:
    """脱敏日志中的敏感信息"""
    # API Key
    message = re.sub(r'X-API-Key:\s*\S+', 'X-API-Key: ***REDACTED***', message)
    # 密码
    message = re.sub(r'password["\s:]+\S+', 'password: ***REDACTED***', message)
    # Token
    message = re.sub(r'token["\s:]+\S+', 'token: ***REDACTED***', message)
    return message
```

### CORS 配置

#### 允许的来源
```yaml
security:
  cors_origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
```

#### FastAPI 中间件
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 速率限制

#### 实现方式
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/")
@limiter.limit("10/minute")
async def handle_jsonrpc(request: Request, ...):
    ...
```

---

## 📊 监控和告警

### 关键指标

#### 业务指标

| 指标名称 | 类型 | 描述 | 告警阈值 |
|----------|------|------|---------|
| `a2a_gateway_tasks_total{status}` | Counter | 任务总数（按状态） | - |
| `a2a_gateway_task_duration_seconds` | Histogram | 任务执行时间分布 | p95 > 5min |
| `a2a_gateway_active_tasks` | Gauge | 当前活跃任务数 | > 10 |
| `a2a_gateway_task_success_rate` | Gauge | 任务成功率（5 分钟窗口） | < 90% |
| `a2a_gateway_tool_invocations_total{tool, skill}` | Counter | 工具调用次数 | - |

#### 系统指标

| 指标名称 | 类型 | 描述 | 告警阈值 |
|----------|------|------|---------|
| `a2a_gateway_http_requests_total{method, status}` | Counter | HTTP 请求数（按方法和状态） | 5xx > 5/min |
| `a2a_gateway_http_request_duration_seconds` | Histogram | HTTP 请求延迟 | p95 > 500ms |
| `a2a_gateway_redis_health` | Gauge | Redis 健康状态（0/1） | 0 |
| `a2a_gateway_redis_latency_seconds` | Gauge | Redis 操作延迟 | > 100ms |
| `process_cpu_seconds_total` | Counter | CPU 使用时间 | > 80% |
| `process_memory_bytes` | Gauge | 内存使用 | > 2GB |

### Prometheus 配置

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'a2a-gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: /metrics
```

### Grafana 仪表板

**关键面板:**

1. **任务概览**
   - 任务总数（按状态）
   - 任务成功率
   - 平均任务执行时间
   - P95 任务执行时间

2. **系统健康**
   - HTTP 请求 QPS
   - HTTP 请求延迟
   - 活跃任务数
   - 错误率

3. **工具使用**
   - 工具调用次数（按工具类型）
   - 工具调用次数（按技能）
   - 工具成功率

4. **资源使用**
   - CPU 使用率
   - 内存使用量
   - Redis 延迟

### 告警规则

**alerting.yml:**
```yaml
groups:
  - name: a2a_gateway_alerts
    interval: 30s
    rules:
      # 任务失败率过高
      - alert: HighTaskFailureRate
        expr: |
          (
            sum(rate(a2a_gateway_tasks_total{status="failed"}[5m]))
            /
            sum(rate(a2a_gateway_tasks_total[5m]))
          ) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "任务失败率超过 10%"
          description: "过去 5 分钟失败率: {{ $value | humanizePercentage }}"

      # HTTP 5xx 错误过多
      - alert: TooManyHttpErrors
        expr: |
          sum(rate(a2a_gateway_http_requests_total{status=~"5.."}[5m])) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "HTTP 5xx 错误过多"
          description: "过去 5 分钟 5xx 错误: {{ $value }}/min"

      # Redis 不可用
      - alert: RedisDown
        expr: a2a_gateway_redis_health == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis 不可用"
          description: "任务数据将无法持久化"

      # 任务执行时间过长
      - alert: SlowTaskExecution
        expr: |
          histogram_quantile(0.95, a2a_gateway_task_duration_seconds) > 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "任务执行时间过长"
          description: "P95 任务执行时间: {{ $value }}s"

      # 活跃任务数过多
      - alert: TooManyActiveTasks
        expr: a2a_gateway_active_tasks > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "活跃任务数过多"
          description: "当前活跃任务: {{ $value }}"

      # CPU 使用率过高
      - alert: HighCPUUsage
        expr: |
          rate(process_cpu_seconds_total[5m]) * 100 > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高"
          description: "CPU 使用率: {{ $value }}%"
```

### 告警通知

**alertmanager.yml:**
```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'default'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        color: 'danger'
```

---

## 📦 版本控制和发布

### 版本号规范

遵循语义化版本（SemVer）：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

示例：
- `1.0.0` → `1.1.0`（新增技能）
- `1.1.0` → `1.1.1`（Bug 修复）
- `1.1.1` → `2.0.0`（API 重大变更）

### 发布流程

#### 1. 开发分支
```bash
# 创建功能分支
git checkout -b feature/add-review-pr-skill

# 开发完成，提交
git add .
git commit -m "feat: add review_pr skill"
git push origin feature/add-review-pr-skill
```

#### 2. Pull Request
- 在 GitHub/GitLab 创建 PR
- 要求至少 1 人 Code Review
- CI 必须通过（测试 + Lint）
- 更新 CHANGELOG.md

#### 3. 合并到 develop
```bash
# PR 通过后，合并到 develop
git checkout develop
git merge feature/add-review-pr-skill
git push origin develop
```

#### 4. 创建 Release
```bash
# 从 develop 创建 release 分支
git checkout -b release/1.1.0

# 更新版本号
# pyproject.toml: version = "1.1.0"
# a2a_gateway/__init__.py: __version__ = "1.1.0"

# 提交
git commit -am "chore: bump version to 1.1.0"

# 合并到 main
git checkout main
git merge release/1.1.0
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags

# 合并回 develop
git checkout develop
git merge main
git push origin develop
```

#### 5. 构建 Docker 镜像
```bash
# 构建
docker build -t a2a-gateway:v1.1.0 .
docker tag a2a-gateway:v1.1.0 a2a-gateway:latest

# 推送
docker push a2a-gateway:v1.1.0
docker push a2a-gateway:latest
```

#### 6. 更新 CHANGELOG.md
```markdown
## [1.1.0] - 2026-01-31

### Added
- review_pr 技能
- Prometheus 指标
- Grafana 仪表板

### Fixed
- PTY 输出解析问题
- Redis 连接池泄漏

### Changed
- 提升并发任务数限制（5 → 10）
```

### 回滚流程

#### 1. 快速回滚（Docker/K8s）
```bash
# Docker
docker-compose pull a2a-gateway:v1.0.0
docker-compose up -d

# Kubernetes
kubectl set image deployment/a2a-gateway gateway=a2a-gateway:v1.0.0
```

#### 2. 数据迁移
```bash
# 如需回退数据，使用 Redis 备份
redis-cli --rdb backup-2026-01-31.rdb
redis-cli --pipe < backup-2026-01-31.rdb
```

---

## 🔄 用户反馈和迭代

### 反馈收集渠道

#### 1. 内部反馈
- Slack 频道 `#all-forai`
- 定期周会复盘
- 邮件反馈

#### 2. 外部反馈
- GitHub Issues
- 用户问卷
- 使用数据分析（日志 + 指标）

### 反馈分类

| 类别 | 处理方式 | 响应时间 |
|------|---------|---------|
| Bug（P0 - 阻塞生产） | 紧急修复 | < 4 小时 |
| Bug（P1 - 影响功能） | 下个版本修复 | < 3 天 |
| 功能需求 | 评估后纳入 Roadmap | < 1 周 |
| 性能问题 | 优化 + 监控 | < 1 周 |
| 文档改进 | 立即更新 | < 2 天 |

### 迭代周期

- **双周迭代**: 每 2 周发布一个版本
- **紧急版本**: 严重 Bug 可随时发布 Hotfix
- **季度规划**: 每 3 个月制定季度 Roadmap

### 迭代流程

```
用户反馈
    ↓
收集分类（Issue Tracker）
    ↓
优先级评估（产品经理）
    ↓
纳入 Sprint（双周）
    ↓
开发 + 测试
    ↓
发布上线
    ↓
用户验证
    ↓
数据收集 + 优化
```

### 数据驱动的优化

#### 关键指标追踪

| 指标 | 目标 | 优化方向 |
|------|------|---------|
| 任务成功率 | > 95% | 提高稳定性 |
| 平均响应时间 | < 30s | 性能优化 |
| API 调用频率 | 稳定增长 | 市场推广 |
| 错误类型分布 | 识别 Top 3 Bug | 优先修复 |

#### 用户行为分析
```python
# 分析用户最常用的技能
skills_usage = db.query("""
    SELECT skill_id, COUNT(*) as count
    FROM tasks
    WHERE created_at > NOW() - INTERVAL 7 DAY
    GROUP BY skill_id
    ORDER BY count DESC
""")
```

---

## 📅 实施计划

### Phase 1: 基础框架 (Week 1)

**目标**: 搭建 A2A 网关基础框架

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 项目初始化（pyproject.toml, 目录结构） | 开发 | P0 | 0.5d |
| 实现 FastAPI 应用 | 开发 | P0 | 1d |
| 实现 Agent Card 服务 | 开发 | P0 | 0.5d |
| 实现 JSON-RPC 基础端点 | 开发 | P0 | 1d |
| 单元测试 | 开发 | P0 | 1d |
| 文档 | 开发 | P0 | 0.5d |

**里程碑**: ✅ A2A Gateway 可启动，响应 Agent Card 请求

### Phase 2: 任务管理 (Week 2)

**目标**: 实现任务生命周期管理

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 实现 TaskStore (InMemory) | 开发 | P0 | 1d |
| 实现 RedisTaskStore | 开发 | P1 | 1d |
| 实现 TaskScheduler | 开发 | P0 | 1d |
| 实现 tasks/send 端点 | 开发 | P0 | 1d |
| 实现 tasks/get 端点 | 开发 | P0 | 1d |
| 并发控制 | 开发 | P1 | 0.5d |
| 单元测试 | 开发 | P0 | 1d |

**里程碑**: ✅ 支持任务创建、查询、状态更新

### Phase 3: PTY 集成 (Week 3)

**目标**: 实现编码工具 PTY 调用

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 实现 PTYProcessManager | 开发 | P0 | 1.5d |
| 实现 OutputParser | 开发 | P0 | 1d |
| 集成 droid | 开发 | P0 | 1d |
| 集成 Claude Code | 开发 | P0 | 1.5d |
| 超时处理 | 开发 | P1 | 0.5d |
| 集成测试 | 开发 | P0 | 1.5d |

**里程碑**: ✅ 成功通过 PTY 调用 droid 和 Claude Code

### Phase 4: 技能实现 (Week 4)

**目标**: 实现具体编码技能

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 实现 fix_bug 技能 | 开发 | P0 | 1d |
| 实现 refactor_code 技能 | 开发 | P0 | 1d |
| 实现 review_pr 技能 | 开发 | P1 | 1d |
| 技能参数验证 | 开发 | P0 | 0.5d |
| E2E 测试 | 开发 | P0 | 1.5d |
| 文档 | 开发 | P0 | 0.5d |

**里程碑**: ✅ 支持至少 3 种编码技能

### Phase 5: 可观测性 (Week 5)

**目标**: 完善监控和日志

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 实现结构化日志 | 开发 | P0 | 0.5d |
| 实现健康检查端点 | 开发 | P0 | 0.5d |
| 实现错误追踪 | 开发 | P1 | 0.5d |
| 实现任务查询 API | 开发 | P0 | 0.5d |
| 集成 Prometheus 指标 | 开发 | P0 | 1d |
| 配置 Grafana 仪表板 | DevOps | P1 | 1d |
| 配置告警规则 | DevOps | P1 | 1d |

**里程碑**: ✅ 完整的可观测性能力

### Phase 6: 安全和部署 (Week 6)

**目标**: 完善安全机制和部署方案

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 实现 API Key 认证 | 开发 | P0 | 0.5d |
| 实现 CORS 配置 | 开发 | P0 | 0.5d |
| 实现速率限制 | 开发 | P1 | 0.5d |
| 实现日志脱敏 | 开发 | P1 | 0.5d |
| 编写 Dockerfile | DevOps | P0 | 0.5d |
| 编写 docker-compose.yml | DevOps | P0 | 0.5d |
| 编写 Kubernetes 清单 | DevOps | P1 | 1d |
| 编写部署文档 | DevOps | P0 | 1d |
| 编写运维文档 | DevOps | P0 | 1d |

**里程碑**: ✅ 可安全部署到生产环境

### Phase 7: 测试与优化 (Week 7)

**目标**: 全面测试和性能优化

| 任务 | 负责人 | 优先级 | 预计时间 |
|------|--------|--------|---------|
| 压力测试 | QA | P0 | 1d |
| 稳定性测试 | QA | P0 | 1d |
| 安全测试 | Security | P1 | 1d |
| 性能优化 | 开发 | P1 | 1d |
| Bug 修复 | 开发 | P0 | 1.5d |
| 文档完善 | 开发 | P0 | 0.5d |
| 发布准备 | 开发 | P0 | 0.5d |

**里程碑**: ✅ 准备发布 v1.0

---

## ⚠️ 风险评估

### 风险矩阵

| 风险 | 影响 | 概率 | 缓解策略 | 负责人 |
|------|------|------|---------|--------|
| PTY 兼容性问题 | 高 | 中 | 充分测试 droid/Claude Code | 开发 |
| 并发任务冲突 | 中 | 中 | 使用 asyncio 任务队列 | 开发 |
| 内存泄漏 | 中 | 低 | 定期清理任务存储 | 开发 |
| 编码工具更新破坏集成 | 高 | 低 | 抽象编码工具接口 | 开发 |
| 任务超时不可控 | 中 | 中 | 可配置超时 + 杀进程 | 开发 |
| 安全性问题 | 高 | 低 | 输入验证 + 日志脱敏 | 开发 |
| 性能瓶颈 | 中 | 中 | 压测 + 异步优化 | 开发 |
| 依赖 a2a-sdk 不稳定 | 中 | 低 | 关注版本更新 | 开发 |
| Redis 单点故障 | 中 | 中 | Redis Sentinel / 集群 | DevOps |
| 监控盲区 | 高 | 低 | 完善告警规则 | DevOps |

### 关键风险详解

#### 风险 1: PTY 兼容性
**描述**: 不同编码工具对 PTY 的要求不同，可能输出格式不兼容。

**缓解**:
- 早期测试 droid 和 Claude Code 的输出格式
- 实现灵活的 OutputParser
- 支持自定义输出解析规则

#### 风险 2: 并发任务冲突
**描述**: 多个任务同时运行可能相互干扰（如端口冲突、文件锁）。

**缓解**:
- 限制并发数量（默认 5）
- 每个任务独立工作目录
- 使用异步任务队列

#### 风险 3: Redis 单点故障
**描述**: 如果使用 Redis，Redis 宕机会导致任务无法持久化。

**缓解**:
- 使用 Redis Sentinel 或集群
- 实现降级机制（Redis 不可用时切换到 InMemory）
- 定期备份 Redis 数据

#### 风险 4: 安全漏洞
**描述**: API 注入、命令注入、敏感信息泄露。

**缓解**:
- 严格的输入验证
- 命令白名单
- 日志脱敏
- 安全测试（OWASP ZAP）

---

## 📚 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| A2A | Agent-to-Agent，标准化 Agent 通信协议 |
| Agent Card | JSON 描述文件，定义 Agent 的能力（技能、接口等） |
| JSON-RPC 2.0 | 远程过程调用协议，基于 JSON |
| PTY | Pseudo Terminal，伪终端，用于模拟交互式终端 |
| Skill | Agent 提供的具体功能（如 fix_bug） |
| Task | 执行单元，包含状态、输入、输出 |
| Artifact | 任务产出的结果（文本、文件等） |
| Prometheus | 开源监控系统，用于指标收集 |
| Grafana | 开源可视化平台，用于仪表板展示 |
| Redis | 开源内存数据存储，用于缓存和持久化 |

### B. 参考资源

- [A2A 协议规范](https://github.com/agentprotocol/a2a)
- [a2a-sdk 文档](https://github.com/agentprotocol/a2a-sdk-python)
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [ptyprocess 文档](https://ptyprocess.readthedocs.io)
- [Prometheus 最佳实践](https://prometheus.io/docs/practices/)
- [Grafana 仪表板](https://grafana.com/docs/grafana/latest/dashboards/)

### C. 配置示例

```toml
# pyproject.toml
[project]
name = "a2a-coding-gateway"
version = "1.0.0"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "a2a-sdk[http-server]>=0.1.0",
    "ptyprocess>=0.7.0",
    "pydantic>=2.0.0",
    "structlog>=23.0.0",
    "prometheus-client>=0.19.0",
    "redis>=5.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

```yaml
# config.yaml
gateway:
  host: "0.0.0.0"
  port: 8000
  max_concurrent_tasks: 5
  default_timeout: 600  # 10 minutes

redis:
  url: "redis://localhost:6379/0"
  enabled: true
  task_retention_days: 7

tools:
  droid:
    command: "droid"
    use_pty: true

  claude:
    command: "claude"
    use_pty: true

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/a2a-gateway/gateway.log"

monitoring:
  metrics_enabled: true
  metrics_port: 8000

security:
  api_key: ${API_KEY}
  cors_origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
```

---

**评审状态**: ⏳ 待评审
**下一步**: 等待大哥评审通过后，进入 Phase 1 开发
