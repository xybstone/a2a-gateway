"""Test script for JSON-RPC endpoints"""

import pytest
from fastapi.testclient import TestClient

from a2a_gateway.main import app

client = TestClient(app)


@pytest.fixture
def created_task_id():
    """Fixture that creates a task and returns its ID"""
    payload = {
        "jsonrpc": "2.0",
        "id": "test-123",
        "method": "tasks/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": '{"bug_description": "Fix the auth module", "workdir": "/project"}'}]
            },
            "skill": "fix_bug"
        }
    }

    response = client.post("/", json=payload)
    result = response.json()
    
    assert "result" in result
    assert "id" in result["result"]
    
    return result["result"]["id"]


def test_tasks_send():
    """Test tasks/send method"""
    payload = {
        "jsonrpc": "2.0",
        "id": "test-123",
        "method": "tasks/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": '{"bug_description": "Fix the auth module", "workdir": "/project"}'}]
            },
            "skill": "fix_bug"
        }
    }

    response = client.post("/", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert "result" in result
    assert "id" in result["result"]
    assert "status" in result["result"]
    assert result["result"]["status"]["state"] == "submitted"


def test_tasks_get(created_task_id):
    """Test tasks/get method"""
    payload = {
        "jsonrpc": "2.0",
        "id": "test-456",
        "method": "tasks/get",
        "params": {"id": created_task_id}
    }

    response = client.post("/", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert "result" in result
    assert result["result"]["id"] == created_task_id
    assert "status" in result["result"]

