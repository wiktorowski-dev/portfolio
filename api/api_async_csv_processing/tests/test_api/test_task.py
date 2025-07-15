from unittest.mock import AsyncMock
import pytest
from types import SimpleNamespace
from datetime import datetime
from uuid import uuid4

from app.crud import task as task_crud
import app.routes.task as task_module


@pytest.mark.asyncio
async def test_get_task_status_success(monkeypatch, async_client):
    # Fake Celery AsyncResult
    class FakeResult:
        def __init__(self, tid):
            self.task_id = tid
            self.status = "SUCCESS"

    monkeypatch.setattr(task_module, "AsyncResult", FakeResult)
    task_id = str(uuid4())

    sql = SimpleNamespace(
        task_id=task_id,
        timestamp=datetime(2025, 7, 10, 15, 0, 0),
        correct_records_count=5,
        incorrect_records_count=1
    )
    monkeypatch.setattr(task_crud, "get_task_details", AsyncMock(return_value=sql))

    resp = await async_client.get("/task/status", params={"task_id": task_id})
    assert resp.status_code == 200
    body = resp.json()

    assert body["task_id"] == task_id
    assert body["task_status"] == {"task_id": task_id, "status": "SUCCESS"}
    assert body["task_details"] == {
        "task_id": sql.task_id,
        "timestamp": sql.timestamp.isoformat(),
        "correct_records_count": sql.correct_records_count,
        "incorrect_records_count": sql.incorrect_records_count
    }


@pytest.mark.asyncio
async def test_get_task_status_missing(monkeypatch, async_client, auth_headers):
    class FakeResult2:
        def __init__(self, tid):
            self.task_id = tid
            self.status = "PENDING"

    monkeypatch.setattr(task_module, "AsyncResult", FakeResult2)
    monkeypatch.setattr(task_crud, "get_task_details", AsyncMock(return_value=None))

    resp = await async_client.get("/task/status", params={"task_id": str(uuid4())}, headers=auth_headers)

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_all_tasks(monkeypatch, async_client, auth_headers):
    from types import SimpleNamespace
    task_id = str(uuid4())
    sample = SimpleNamespace(
        task_id=task_id,
        timestamp=datetime(2025, 7, 11, 8, 30, 0),
        correct_records_count=2,
        incorrect_records_count=0
    )
    # Stub list_tasks to return a singleton list
    monkeypatch.setattr(task_crud, "list_tasks", AsyncMock(return_value=[sample]))

    resp = await async_client.get("/task/tasks", params={"page": 1, "limit": 10}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0] == {
        "task_id": sample.task_id,
        "timestamp": sample.timestamp.isoformat(),
        "correct_records_count": sample.correct_records_count,
        "incorrect_records_count": sample.incorrect_records_count
    }
