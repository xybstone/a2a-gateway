# 附录

## A. 术语表

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

## B. 参考资源

- [A2A 协议规范](https://github.com/agentprotocol/a2a)
- [a2a-sdk 文档](https://github.com/agentprotocol/a2a-sdk-python)
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [ptyprocess 文档](https://ptyprocess.readthedocs.io)
- [Prometheus 最佳实践](https://prometheus.io/docs/practices/)
- [Grafana 仪表板](https://grafana.com/docs/grafana/latest/dashboards/)

## C. 配置示例

### pyproject.toml

```toml
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

### config.yaml

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
