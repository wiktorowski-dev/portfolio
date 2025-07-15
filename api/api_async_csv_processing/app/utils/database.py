from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker


def _get_db_url(user, password, host, port, db) -> str:
    return (
        f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    )



def create_async_db_connection(user, password, host, port, db) -> AsyncSession:
    db_url = _get_db_url(user, password, host, port, db)

    engine = create_async_engine(db_url, echo=True)
    session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return session


def create_async_db_engine(user, password, host, port, db) -> AsyncEngine:
    db_url = _get_db_url(user, password, host, port, db)
    return create_async_engine(db_url, echo=True)
