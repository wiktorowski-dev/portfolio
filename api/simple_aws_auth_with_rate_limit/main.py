import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from time import time as current_time
from collections import defaultdict
# from app.routers import api_router
from app.routers import v1_router, auth_router

app = FastAPI(
    title="Backend API",
    version="0.0.1"
)
origins = [
    "*"  # allow everyone for development; restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(v1_router, prefix='/api/v1', tags=['v1'])
app.include_router(auth_router, prefix='/auth', tags=['auth'])

request_times = defaultdict(list)


def rate_limit(ip: str, times: int, seconds: int):
    current_time_in_sec = current_time()
    request_times[ip] = [t for t in request_times[ip] if current_time_in_sec - t < seconds]

    if len(request_times[ip]) >= times:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    request_times[ip].append(current_time_in_sec)


@app.middleware("http")
async def limit_requests(request: Request, call_next):
    if os.getenv("ENV") == "pytest":
        return await call_next(request)

    ip = request.client.host
    try:
        rate_limit(ip, times=100, seconds=60)

        response = await call_next(request)
        return response
    except HTTPException as e:
        if e.status_code == 429:
            return JSONResponse(
                status_code=429,
                content={"detail": e.detail}
            )
        raise e


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/sign_in")
async def sign_in():
    return RedirectResponse(url="/auth/sign_in")


@app.post("/sign_up")
async def sign_up():
    return RedirectResponse(url="/auth/sign_up")


def check_env_variables(required_envs: list[str]):
    missing_vars = [var for var in required_envs if var not in os.environ]

    if missing_vars:
        raise KeyError(f"Missing required environment variables: {', '.join(missing_vars)}")


if __name__ == '__main__':
    check_env_variables(['SQL_SCHEMA', 'sql_secret', 'cognito_secret'])
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
