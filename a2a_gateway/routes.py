"""API routes for A2A Coding Gateway"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from a2a_gateway.a2a_sdk import get_agent_card
from a2a_gateway.config import settings
from a2a_gateway.tasks import task_store
from a2a_gateway.tools import execute_task_with_tool

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


class JSONRPCRequest(BaseModel):
    """JSON-RPC request model"""

    jsonrpc: str
    id: str
    method: str
    params: Dict[str, Any]


class JSONRPCResponse(BaseModel):
    """JSON-RPC response model"""

    jsonrpc: str = "2.0"
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@router.get("/.well-known/agent.json")
async def get_agent_card_endpoint():
    """Return A2A Agent Card"""
    return get_agent_card()


@router.post("/")
@limiter.limit("10/minute")
async def jsonrpc_endpoint(request: Request, jsonrpc_request: JSONRPCRequest):
    """Handle JSON-RPC requests"""
    try:
        # API Key authentication
        if settings.api_key:
            api_key = request.headers.get("X-API-Key")
            if api_key != settings.api_key:
                return JSONRPCResponse(
                    id=jsonrpc_request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params",
                        "data": "Invalid API Key",
                    },
                )

        if jsonrpc_request.method == "tasks/send":
            return await handle_tasks_send(jsonrpc_request)
        elif jsonrpc_request.method == "tasks/get":
            return await handle_tasks_get(jsonrpc_request)
        else:
            raise HTTPException(status_code=404, detail="Method not found")
    except Exception as e:
        return JSONRPCResponse(
            id=jsonrpc_request.id,
            error={"code": -32603, "message": "Internal error", "data": str(e)},
        )


async def handle_tasks_send(request: JSONRPCRequest) -> JSONRPCResponse:
    """Handle tasks/send method"""
    params = request.params
    message = params.get("message")
    skill = params.get("skill")

    if not message or not skill:
        return JSONRPCResponse(
            id=request.id,
            error={
                "code": -32602,
                "message": "Invalid params",
                "data": "Missing required fields: message or skill",
            },
        )

    # Create task
    task_id = await task_store.create_task(message=message, skill=skill)

    return JSONRPCResponse(
        id=request.id,
        result={
            "id": task_id,
            "status": {
                "state": "submitted",
                "timestamp": await task_store.get_task_timestamp(task_id),
            },
        },
    )


async def handle_tasks_get(request: JSONRPCRequest) -> JSONRPCResponse:
    """Handle tasks/get method"""
    params = request.params
    task_id = params.get("id")

    if not task_id:
        return JSONRPCResponse(
            id=request.id,
            error={
                "code": -32602,
                "message": "Invalid params",
                "data": "Missing required field: id",
            },
        )

    # Get task
    task = await task_store.get_task(task_id)
    if not task:
        return JSONRPCResponse(
            id=request.id,
            error={
                "code": -32000,
                "message": "Task not found",
                "data": f"Task with id {task_id} not found",
            },
        )

    # If task is submitted, start execution in background
    if task["status"]["state"] == "submitted":
        await task_store.update_task_status(task_id, "working")
        # Execute task asynchronously without blocking
        import asyncio

        asyncio.create_task(
            execute_task_with_tool(task_id, task["message"], task["skill"])
        )
        # Return updated task status
        task = await task_store.get_task(task_id)

    return JSONRPCResponse(id=request.id, result=task)
