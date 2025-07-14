from contextlib import AsyncExitStack, asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# from app.routers import api_router
from app.core import settings
from app import routes



@asynccontextmanager
async def setup_sql(app: FastAPI):
    try:

        db_url = (
            f"postgresql+asyncpg://"
            f"{settings.postgres_user}:{settings.postgres_password}"
            f"@"
            f"{settings.postgres_host}:{settings.postgres_port}"
            f"/{settings.postgres_db}"
        )

        engine = create_async_engine(db_url, echo=True)
        session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        app.state.sql_session = session

        yield
    finally:
        pass


@asynccontextmanager
async def setup_lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(setup_sql(app))
        yield

app = FastAPI(
    title="API Async csv processing",
    version="0.0.1",
    lifespan=setup_lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Specify allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(routes.auth, prefix='/auth', tags=['auth'])
app.include_router(routes.reports, prefix='/reports', tags=['reports'])
app.include_router(routes.transactions, prefix='/transactions', tags=['transactions'])


@app.get("/health")
async def health():
    return Response(status_code=200, content='')



if __name__ == '__main__':
    import uvicorn
    workers = 1
    print(f'Using workers: {workers}')
    uvicorn.run("main:app", host="0.0.0.0", port=8080, workers=workers)
