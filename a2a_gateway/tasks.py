"""Task management for A2A Coding Gateway"""

import uuid
import asyncio
from typing import Any, Dict, Optional

from a2a_gateway.config import settings
from a2a_gateway.redis_store import RedisTaskStore
from a2a_gateway.memory_store import InMemoryTaskStore


# Concurrency control for task execution
task_semaphore = asyncio.BoundedSemaphore(settings.max_concurrent_tasks)


class TaskStore:
    """Abstract task store interface"""

    def __init__(self):
        if settings.redis_enabled and settings.redis_url:
            self.store = RedisTaskStore(settings.redis_url)
        else:
            self.store = InMemoryTaskStore()

    async def initialize(self):
        """Initialize task store"""
        await self.store.initialize()

    async def close(self):
        """Close task store"""
        await self.store.close()

    async def create_task(self, message: Dict[str, Any], skill: str) -> str:
        """Create a new task"""
        task_id = str(uuid.uuid4())
        await self.store.create_task(task_id, message, skill)
        return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        return await self.store.get_task(task_id)

    async def update_task_status(self, task_id: str, status: str):
        """Update task status"""
        await self.store.update_task_status(task_id, status)

    async def update_task_result(self, task_id: str, result: Dict[str, Any]):
        """Update task result"""
        await self.store.update_task_result(task_id, result)

    async def get_task_timestamp(self, task_id: str) -> str:
        """Get task timestamp"""
        return await self.store.get_task_timestamp(task_id)

    async def get_active_count(self) -> int:
        """Get number of active tasks"""
        return await self.store.get_active_count()

    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health (if using Redis store)"""
        if isinstance(self.store, RedisTaskStore):
            return await self.store.check_health()
        return {"status": "not_used"}

    @property
    def active_count(self) -> int:
        """Get number of active tasks (sync version for health check)"""
        return self.store.active_count


task_store = TaskStore()
