# 监控和告警

## 监控系统架构

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

#### 关键面板

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
