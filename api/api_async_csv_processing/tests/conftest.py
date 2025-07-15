import asyncio

import importlib
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import main
from main import app
from app.models.base import Base
from app.dependencies.auth import get_current_user
from app.dependencies.db_session import get_db_session


TEST_ENVS = {
    "postgres_user":     "test_user",
    "postgres_password": "test_pass",
    "postgres_host":     "localhost",
    "postgres_port":     "5432",
    "transactions_db":   "test_db",
    "celery_broker_uri": "redis://localhost:6379",
}

@pytest.fixture(autouse=True)
def set_env_vars_and_reload(monkeypatch):
    for k, v in TEST_ENVS.items():
        monkeypatch.setenv(k, v)

    from app.core.settings import get_settings
    get_settings.cache_clear()

    import celery_app
    importlib.reload(celery_app)

    yield


@pytest.fixture(scope="function")
def event_loop():
    """Create a fresh asyncio loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def engine():
    """In-memory SQLite async engine."""
    url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
def session_factory(engine):
    """Returns an async session factory bound to the in-memory engine."""
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
def override_db_dependency(session_factory):
    """
    Override the `get_db_session` dependency in all routes to use our in-memory session.
    """
    main.app.dependency_overrides[get_db_session] = lambda: session_factory
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture
async def client():
    """An HTTP client against our FastAPI app."""
    async with AsyncClient(app=main.app, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="function")
async def async_client(session_factory):
    # Override DB session dependency to yield a no‐op
    async def override_db_session():
        yield session_factory

    # Override auth dependency to always return a fixed test user
    async def override_current_user():
        return "test@example.com"

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user] = override_current_user

    # Spin up the test client
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(scope="function")
async def auth_headers(async_client):
    # Register user
    payload = {"email": "new@example.com", "password": "Password1!"}
    resp = await async_client.post("/auth/sign_up", json=payload)
    assert resp.status_code == 201

    # Sign in
    resp = await async_client.post(
        "/auth/sign_in",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )
    assert resp.status_code == 200

    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
