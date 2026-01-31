"""In-memory task store implementation"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class InMemoryTaskStore:
    """In-memory task store implementation"""

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def initialize(self):
        """Initialize task store"""
        pass

    async def close(self):
        """Close task store"""
        pass

    async def create_task(self, task_id: str, message: Dict[str, Any], skill: str):
        """Create a new task"""
        async with self.lock:
            self.tasks[task_id] = {
                "id": task_id,
                "message": message,
                "skill": skill,
                "status": {
                    "state": "submitted",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": None,
                },
                "artifacts": [],
                "created_at": datetime.utcnow().isoformat(),
            }

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        async with self.lock:
            return self.tasks.get(task_id)

    async def update_task_status(self, task_id: str, status: str):
        """Update task status"""
        async with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"]["state"] = status
                self.tasks[task_id]["status"][
                    "timestamp"
                ] = datetime.utcnow().isoformat()

    async def update_task_result(self, task_id: str, result: Dict[str, Any]):
        """Update task result"""
        async with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]["artifacts"] = result.get("artifacts", [])
                if "error" in result:
                    self.tasks[task_id]["status"]["error"] = result["error"]

    async def get_task_timestamp(self, task_id: str) -> str:
        """Get task timestamp"""
        async with self.lock:
            if task_id in self.tasks:
                return self.tasks[task_id]["status"]["timestamp"]
            return datetime.utcnow().isoformat()

    async def get_active_count(self) -> int:
        """Get number of active tasks"""
        async with self.lock:
            active_tasks = [
                task
                for task in self.tasks.values()
                if task["status"]["state"] in ["submitted", "working"]
            ]
            return len(active_tasks)

    @property
    def active_count(self) -> int:
        """Get number of active tasks (sync version)"""
        active_tasks = [
            task
            for task in self.tasks.values()
            if task["status"]["state"] in ["submitted", "working"]
        ]
        return len(active_tasks)
