import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from types import SimpleNamespace

from app.crud import transactions
from app import exceptions


@pytest.mark.asyncio
async def test_get_transaction_success(monkeypatch, async_client):
    dummy = {
        "transaction_id": str(uuid4()),
        "timestamp": "2025-07-01T12:00:00",
        "amount": 42.0,
        "currency": "USD",
        "customer_id": str(uuid4()),
        "product_id": str(uuid4()),
        "quantity": 7
    }
    monkeypatch.setattr(transactions, "get_transaction_details", AsyncMock(return_value=dummy))

    resp = await async_client.get(f"/transactions/{dummy['transaction_id']}")
    assert resp.status_code == 200
    assert resp.json() == dummy


@pytest.mark.asyncio
async def test_get_transaction_missing(monkeypatch, async_client, auth_headers):
    monkeypatch.setattr(transactions, "get_transaction_details", AsyncMock(return_value=None))
    resp = await async_client.get(f"/transactions/{str(uuid4())}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == exceptions.MISSING_TRANSACTION.detail


@pytest.mark.asyncio
async def test_list_transactions(monkeypatch, async_client, auth_headers):
    items = [
        {
            "transaction_id": str(uuid4()),
            "timestamp": "2025-07-02T08:30:00",
            "amount": 10.0,
            "currency": "EUR",
            "customer_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1
        },
        {
            "transaction_id": str(uuid4()),
            "timestamp": "2025-07-03T09:45:00",
            "amount": 20.0,
            "currency": "GBP",
            "customer_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 2
        }
    ]
    monkeypatch.setattr(transactions, "list_transactions", AsyncMock(return_value=(2, items)))

    resp = await async_client.get("/transactions", params={"page": 1, "limit": 5}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["limit"] == 5
    assert body["items"] == items


@pytest.mark.asyncio
async def test_upload_transactions_file_success(monkeypatch, async_client, auth_headers):
    task_id = str(uuid4())
    fake = SimpleNamespace(task_id=task_id, status="PENDING")

    monkeypatch.setattr("app.routes.transactions.process_transactions_file", AsyncMock(return_value=fake))

    csv_bytes = b"a,b,c\n1,2,3"
    files = {"file": ("data.csv", csv_bytes, "text/csv")}
    resp = await async_client.post("/transactions/upload", files=files, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"task_id": fake.task_id, "status": fake.status}


@pytest.mark.asyncio
async def test_upload_transactions_file_bad_type(async_client, auth_headers):
    files = {"file": ("data.txt", b"x,y,z", "text/plain")}
    resp = await async_client.post("/transactions/upload", files=files, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == exceptions.INCORRECT_FILE_TYPE.detail
