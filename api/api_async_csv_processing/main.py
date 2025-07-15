from contextlib import AsyncExitStack, asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core import settings
from app import routes, utils
from app.utils import database
from app.models import base



@asynccontextmanager
async def setup_sql(app: FastAPI):
    try:
        db_connection_kwargs = dict(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            db=settings.postgres_db
        )

        session_factory  = database.create_async_db_connection(**db_connection_kwargs)
        app.state.session_factory = session_factory

        # Create databases
        engine = database.create_async_db_engine(**db_connection_kwargs)
        async with engine.begin() as conn:
            await conn.run_sync(base.Base.metadata.create_all)

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
app.include_router(routes.task, prefix='/task', tags=['task'])


@app.get("/health")
async def health():
    return Response(status_code=200, content='')



if __name__ == '__main__':
    import uvicorn
    workers = 1
    print(f'Using workers: {workers}')
    uvicorn.run("main:app", host="0.0.0.0", port=8080, workers=workers)
