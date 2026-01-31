# A2A 协议支持

## FR1: A2A 协议支持

### FR1.1 Agent Card

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

### FR1.2 JSON-RPC 2.0 端点

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

### FR1.3 任务生命周期

任务状态必须支持：

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `submitted` | 任务已接收，未开始 | `tasks/send` 成功 |
| `working` | 任务执行中 | 编码工具启动 |
| `completed` | 任务成功完成 | 编码工具返回结果 |
| `failed` | 任务失败 | 编码工具出错或超时 |
| `canceled` | 任务被取消 | 用户取消任务 |
