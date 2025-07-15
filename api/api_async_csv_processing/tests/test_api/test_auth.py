import pytest
from unittest.mock import AsyncMock

from app.crud import users
from app.utils import auth as auth_utils
from app import exceptions


@pytest.mark.asyncio
async def test_sign_up_success(monkeypatch, async_client):
    monkeypatch.setattr(users, "get_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(users, "create_user", AsyncMock(return_value=None))

    payload = {"email": "new@example.com", "password": "Password1!"}
    resp = await async_client.post("/auth/sign_up", json=payload)
    assert resp.status_code == 201
    assert resp.json() == {"email": payload["email"]}


@pytest.mark.asyncio
async def test_sign_up_already_exists(monkeypatch, async_client):
    monkeypatch.setattr(users, "get_user_by_email", AsyncMock(return_value=object()))

    resp = await async_client.post("/auth/sign_up", json={"email": "dup@example.com", "password": "Password1!"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == exceptions.USER_ALREADY_EXISTS.detail


@pytest.mark.asyncio
async def test_sign_in_success(monkeypatch, async_client):
    class DummyUser:
        email = "joe@example.com"
        password_hash = auth_utils.hash_password("rightpass")

    monkeypatch.setattr(users, "get_user_by_email", AsyncMock(DummyUser()))

    monkeypatch.setattr(auth_utils, "verify_password", lambda plain, hashed: True)

    monkeypatch.setattr(auth_utils, "create_access_token", lambda data: "tok123")

    data = {"username": "joe@example.com", "password": "rightpass"}
    resp = await async_client.post("/auth/sign_in", data=data)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and body["access_token"] == "tok123"


@pytest.mark.asyncio
async def test_sign_in_invalid(monkeypatch, async_client):
    monkeypatch.setattr(users, "get_user_by_email", AsyncMock(return_value=None))
    resp = await async_client.post("/auth/sign_in", data={"username": "x", "password": "y"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == exceptions.INVALID_CREDENTIALS.detail
