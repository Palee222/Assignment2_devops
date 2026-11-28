import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .database import check_database_health, init_db
from .routes import router

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), stream=sys.stdout)
logger = logging.getLogger("incidents-service")


@asynccontextmanager
async def lifespan(_: FastAPI):
    for attempt in range(1, 13):
        try:
            init_db()
            break
        except SQLAlchemyError:
            if attempt == 12:
                raise
            time.sleep(min(5 * attempt, 30))
    yield


app = FastAPI(title="Incidents Service", version="1.0.0", lifespan=lifespan)
configured_origins = os.getenv("CORS_ALLOWED_ORIGINS")
allowed_origins = (
    ["http://localhost:5173", "http://127.0.0.1:5173"]
    if configured_origins is None
    else [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
)
for origin in allowed_origins:
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
        or "*" in origin
    ):
        raise ValueError(
            f"Invalid CORS origin {origin!r}; configure scheme and host only."
        )
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.middleware("http")
async def log_request(request: Request, call_next):
    started_at = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "%s",
            json.dumps(
                {
                    "event": "request",
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
                separators=(",", ":"),
            ),
        )


@app.get("/health", tags=["health"])
def health():
    git_sha = os.getenv("GIT_SHA", "unknown")
    try:
        check_database_health()
    except (SQLAlchemyError, RuntimeError):
        logger.exception("Incidents service database health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "unavailable",
                "git_sha": git_sha,
            },
        )
    return {"status": "ok", "database": "ok", "git_sha": git_sha}
