```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```

## Project Overview

A2A Coding Gateway for Clawdbot - a FastAPI-based service that implements the A2A protocol for standardized communication between agents, with built-in support for coding tools like droid and Claude Code via PTY terminal integration.

## Technology Stack

- **HTTP Framework**: FastAPI
- **A2A Protocol**: a2a-sdk
- **Terminal Handling**: ptyprocess
- **Async Runtime**: asyncio

## Key Features

### A2A Protocol Support
- Agent Card endpoint: `/.well-known/agent.json`
- JSON-RPC 2.0 API:
  - `tasks/send` - Send tasks to the gateway
  - `tasks/get` - Retrieve task results

### Coding Tool Integration
- droid (PTY mode)
- Claude Code (PTY mode)

## Current State

This repository is in the initial planning phase. The PRD (Product Requirements Document) is available at `/tmp/a2a-gateway-prd.md` (reference in README.md).

## Future Development

When implementing this project, focus on:
1. Creating a FastAPI application with the required endpoints
2. Integrating the a2a-sdk for protocol handling
3. Implementing PTY terminal management for coding tool execution
4. Ensuring reliable asyncio-based task processing

## Configuration Files

- `.gitignore` - Git ignore rules (Python, macOS, VS Code, etc.)
- `README.md` - Project overview and PRD reference
- `LICENSE` - Project license file
