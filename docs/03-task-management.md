# 任务管理

## FR4: 任务管理

### FR4.1 任务存储

- 默认内存存储（InMemoryTaskStore）
- 可选 Redis 持久化
- 支持并发任务
- 任务 ID 使用 UUID

### FR4.2 并发控制

- 支持最多 5 个并发任务
- 超出限制时返回错误
- 可配置并发数量

### FR4.3 超时处理

- 默认超时 10 分钟
- 可通过参数调整
- 超时后任务状态变为 `failed`

## FR5: 数据持久化

### FR5.1 Redis 集成

- 可选的 Redis 后端用于任务持久化
- 支持任务状态保存到 Redis
- 服务重启后恢复未完成任务
- 配置开关控制是否启用

### FR5.2 数据模型

```python
# Redis Key 格式
task:{task_id} → Task 对象（JSON 序列化）
tasks:pending → ZSET（按创建时间排序）
tasks:working → ZSET
tasks:completed → ZSET
tasks:failed → ZSET
```

### FR5.3 数据清理

- 完成的任务保留 24 小时
- 失败的任务保留 7 天
- 自动清理过期数据
- 可配置保留时间
