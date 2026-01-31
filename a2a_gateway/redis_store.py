"""Redis task store implementation"""

import asyncio
import json
from datetime import datetime, UTC
from typing import Any, Dict, Optional

import redis.asyncio as redis


class RedisTaskStore:
    """Redis task store implementation"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self.pool: Optional[redis.ConnectionPool] = None

    async def initialize(self):
        """Initialize Redis connection"""
        self.pool = redis.ConnectionPool.from_url(self.redis_url)
        self.client = redis.Redis(connection_pool=self.pool)

    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()

    async def create_task(self, task_id: str, message: Dict[str, Any], skill: str):
        """Create a new task in Redis"""
        task_data = {
            "id": task_id,
            "message": message,
            "skill": skill,
            "status": {
                "state": "submitted",
                "timestamp": datetime.now(UTC).isoformat(),
                "error": None,
            },
            "artifacts": [],
            "created_at": datetime.now(UTC).isoformat(),
        }

        pipe = self.client.pipeline()
        pipe.set(f"task:{task_id}", json.dumps(task_data))
        pipe.zadd("tasks:pending", {task_id: datetime.now(UTC).timestamp()})
        await pipe.execute()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID from Redis"""
        task_data = await self.client.get(f"task:{task_id}")
        if task_data:
            return json.loads(task_data)
        return None

    async def update_task_status(self, task_id: str, status: str):
        """Update task status in Redis"""
        task = await self.get_task(task_id)
        if task:
            task["status"]["state"] = status
            task["status"]["timestamp"] = datetime.now(UTC).isoformat()

            # Move task between status sets
            pipe = self.client.pipeline()
            pipe.set(f"task:{task_id}", json.dumps(task))

            # Remove from old status set
            for status_set in [
                "tasks:pending",
                "tasks:working",
                "tasks:completed",
                "tasks:failed",
            ]:
                pipe.zrem(status_set, task_id)

            # Add to new status set
            if status == "submitted":
                pipe.zadd("tasks:pending", {task_id: datetime.now(UTC).timestamp()})
            elif status == "working":
                pipe.zadd("tasks:working", {task_id: datetime.now(UTC).timestamp()})
            elif status == "completed":
                pipe.zadd("tasks:completed", {task_id: datetime.now(UTC).timestamp()})
            elif status == "failed":
                pipe.zadd("tasks:failed", {task_id: datetime.now(UTC).timestamp()})

            await pipe.execute()

    async def update_task_result(self, task_id: str, result: Dict[str, Any]):
        """Update task result in Redis"""
        task = await self.get_task(task_id)
        if task:
            task["artifacts"] = result.get("artifacts", [])
            if "error" in result:
                task["status"]["error"] = result["error"]
            await self.client.set(f"task:{task_id}", json.dumps(task))

    async def get_task_timestamp(self, task_id: str) -> str:
        """Get task timestamp from Redis"""
        task = await self.get_task(task_id)
        if task:
            return task["status"]["timestamp"]
        return datetime.now(UTC).isoformat()

    async def get_active_count(self) -> int:
        """Get number of active tasks from Redis"""
        pending_count = await self.client.zcard("tasks:pending")
        working_count = await self.client.zcard("tasks:working")
        return pending_count + working_count

    async def check_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            pong = await self.client.ping()
            if pong:
                info = await self.client.info()
                return {
                    "status": "healthy",
                    "version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                }
            return {"status": "unhealthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @property
    def active_count(self) -> int:
        """Get number of active tasks (sync version)"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_active_count())
