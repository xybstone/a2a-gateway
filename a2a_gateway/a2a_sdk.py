"""Mock A2A SDK implementation for testing purposes"""

from typing import Any, Dict

# Mock Agent Card response
MOCK_AGENT_CARD = {
    "name": "ClawdbotCodingAgent",
    "description": "Fixes bugs, refactors code, and reviews PRs",
    "url": "http://localhost:8000",
    "interfaces": [{"url": "http://localhost:8000", "transport": "JSONRPC"}],
    "capabilities": {"streaming": False, "pushNotifications": False},
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
                    "context_files": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["bug_description"],
            },
        }
    ],
}


class A2AClient:
    """Mock A2A client"""

    def __init__(self, url: str = "http://localhost:8000"):
        self.url = url

    async def send_task(self, message: Dict[str, Any], skill: str) -> Dict[str, Any]:
        """Mock send task method"""
        return {
            "id": "mock-task-id-123",
            "status": {"state": "submitted", "timestamp": "2026-01-31T14:00:00Z"},
        }

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Mock get task method"""
        return {
            "id": task_id,
            "status": {
                "state": "completed",
                "timestamp": "2026-01-31T14:05:00Z",
                "error": None,
            },
            "artifacts": [
                {
                    "type": "data",
                    "data": {
                        "summary": "Mock task result",
                        "files_changed": ["src/mock.py"],
                        "diff": "...",
                    },
                }
            ],
        }


def create_a2a_client(url: str) -> A2AClient:
    """Create a mock A2A client instance"""
    return A2AClient(url)


def get_agent_card() -> Dict[str, Any]:
    """Get the mock Agent Card"""
    return MOCK_AGENT_CARD
