# 可观测性

## FR7: 可观测性

### FR7.1 健康检查

- `/health` 端点
- 返回服务状态和版本信息
- 检查 Redis 连接（如果启用）

### FR7.2 任务查询

- 支持通过 `tasks/get` 查询任务状态
- 返回完整任务信息（状态、进度、结果）
- 支持批量查询

### FR7.3 日志记录

- 结构化日志（JSON 格式）
- 包含时间戳、级别、消息、上下文
- 日志级别可配置
- 日志输出到 stdout + 文件

### FR7.4 Prometheus 指标

- `/metrics` 端点暴露 Prometheus 格式指标
- 关键指标：
  - `a2a_gateway_tasks_total{status}`: 任务总数（按状态）
  - `a2a_gateway_task_duration_seconds`: 任务执行时间
  - `a2a_gateway_active_tasks`: 当前活跃任务数
  - `a2a_gateway_http_requests_total{method, status}`: HTTP 请求数
  - `a2a_gateway_tool_invocations_total{tool, skill}`: 工具调用次数
  - `a2a_gateway_redis_health`: Redis 健康状态（0/1）
