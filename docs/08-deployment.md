# 部署和运维

## 环境要求

### 最小配置

- CPU: 2 核
- 内存: 2 GB
- 磁盘: 10 GB
- Python: 3.11+
- Redis: 可选（如需持久化）

### 推荐配置

- CPU: 4 核
- 内存: 4 GB
- 磁盘: 50 GB
- Redis: 单机实例

## 部署方式

### 方式 1: Docker 容器部署

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

### 方式 2: Kubernetes 部署

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

### 方式 3: Systemd 服务（Linux）

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

## 配置管理

### 环境变量

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

## 运维指南

### 健康检查

```bash
# 基本健康检查
curl http://localhost:8000/health

# 详细健康检查（包括 Redis）
curl http://localhost:8000/health?detailed=true
```

### 日志查看

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

### 重启服务

```bash
# Docker
docker-compose restart gateway

# Kubernetes
kubectl rollout restart deployment/a2a-gateway

# Systemd
sudo systemctl restart a2a-gateway
```

### 性能监控

```bash
# 查看 Prometheus 指标
curl http://localhost:8000/metrics

# 查看当前活跃任务
curl http://localhost:8000/metrics | grep a2a_gateway_active_tasks

# 查看任务成功率
curl http://localhost:8000/metrics | grep a2a_gateway_tasks_total
```

### 数据清理

```bash
# 手动清理 Redis 中的过期任务
redis-cli --scan --pattern "task:*" | xargs -L 1000 redis-cli DEL

# 清理特定状态的任务
redis-cli --scan --pattern "tasks:failed:*" | xargs -L 1000 redis-cli DEL
```
