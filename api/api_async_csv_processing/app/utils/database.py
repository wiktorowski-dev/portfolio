from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session


def create_async_db_connection(user, password, host, port, db):
        db_url = (
            f"postgresql+asyncpg://"
            f"{user}:{password}"
            f"@"
            f"{host}:{port}"
            f"/{db}"
        )

        engine = create_async_engine(db_url, echo=True)
        session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        return session


def create_sync_db_connection(user, password, host, port, db):
        db_url = (
            f"postgresql+asyncpg://"
            f"{user}:{password}"
            f"@"
            f"{host}:{port}"
            f"/{db}"
        )

        engine = create_async_engine(db_url, echo=True)
        sync_engine = engine.sync_engine  # <─ key line!
        session = Session(bind=sync_engine, class_=AsyncSession, expire_on_commit=False)
        return session
