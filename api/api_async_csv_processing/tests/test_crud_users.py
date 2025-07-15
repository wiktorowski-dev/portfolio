import pytest
from app.crud.users import create_user, get_user_by_email


@pytest.mark.asyncio
async def test_create_and_get_user(session_factory):
    email = "alex@example.com"
    pw_hash = "dummyhash"

    user = await create_user(session_factory, email, pw_hash)
    assert user.email == email
    assert user.password_hash == pw_hash

    fetched = await get_user_by_email(session_factory, email)
    assert fetched is not None
    assert fetched.email == email
    assert fetched.password_hash == pw_hash


@pytest.mark.asyncio
async def test_get_nonexistent_user(session_factory):
    missing = await get_user_by_email(session_factory, "not-user@example.com")
    assert missing is None
