import pytest


@pytest.mark.asyncio
async def test_read_users_me(async_client):
    resp = await async_client.get("/user/me")
    assert resp.status_code == 200
    
    assert resp.json() == {"email": "test@example.com"}
