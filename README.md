# a2a-gateway

完整文档在: a2a-gateway-prd-v2.md

---

# 📋 A2A 编码网关 PRD

## 🎯 项目概览

项目名称: A2A Coding Gateway for Clawdbot
版本: v1.0
状态: 待评审

### 核心目标

1. 标准化通信: 实现 A2A 协议
2. 简化集成: 无需 Temporal
3. 可靠执行: PTY 终端处理

---

## 🏗️ 技术架构

- FastAPI (HTTP 框架)
- a2a-sdk (A2A 协议)
- ptyprocess (PTY 终端)
- asyncio (异步运行时)

---

## 🔧 功能需求 (FR)

### FR1: A2A 协议支持

- Agent Card: /.well-known/agent.json
- JSON-RPC 2.0: tasks/send, tasks/get

### FR2: 编码工具集成

- droid (PTY 模式)
- Claude Code (PTY 模式)

</aside>
