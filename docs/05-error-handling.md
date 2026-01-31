# 错误处理

## FR6: 错误处理

### FR6.1 错误日志

- 记录所有任务错误
- 包含任务 ID、错误类型、堆栈信息
- 日志级别：ERROR
- 错误日志持久化到 Redis

### FR6.2 错误返回

- JSON-RPC 错误格式
- 包含错误代码和消息
- 区分业务错误和系统错误

### FR6.3 重试机制

- 可选的任务重试
- 最多重试 3 次
- 指数退避策略

### 错误代码

| 代码 | 含义 | 场景 |
|------|------|------|
| -32700 | Parse error | JSON 解析失败 |
| -32600 | Invalid Request | 不是有效的 JSON-RPC 请求 |
| -32601 | Method not found | 方法不存在 |
| -32602 | Invalid params | 参数验证失败 |
| -32603 | Internal error | 服务器内部错误 |
| -32000 | Task not found | 任务 ID 不存在 |
| -32001 | Tool not supported | 编码工具不支持 |
| -32002 | Timeout | 任务超时 |
| -32003 | Concurrent limit reached | 并发任务超出限制 |
