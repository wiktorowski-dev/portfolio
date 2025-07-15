import pytest
import uuid
from fastapi import status


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.text == ""


@pytest.mark.asyncio
async def test_sign_up_and_sign_in_flow(client):
    email = "charlie@example.com"
    password = "Test#1234"

    # sign up
    r1 = await client.post("/auth/sign_up", json={"email": email, "password": password})
    assert r1.status_code == status.HTTP_201_CREATED

    # duplicate sign up
    r1b = await client.post("/auth/sign_up", json={"email": email, "password": password})
    assert r1b.status_code == status.HTTP_400_BAD_REQUEST

    # sign in
    r2 = await client.post(
        "/auth/sign_in",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == status.HTTP_200_OK
    body = r2.json()
    assert "access_token" in body and body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    # no token → 401
    cid = uuid.uuid4()
    r = await client.get(f"/reports/customer-summary/{cid}")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
