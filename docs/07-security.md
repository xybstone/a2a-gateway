# 安全设计

## 安全架构

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
