from contextlib import asynccontextmanager
from time import time

import structlog
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routers.auth import router as auth_router
from app.api.routers.schedules import router as schedules_router
from app.api.routers.telemetry import router as telemetry_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routes.playbooks import router as playbooks_router
from app.services.bootstrap import init_db

settings = get_settings()
configure_logging(settings.log_level, settings.json_logs)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db(seed=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(playbooks_router, prefix=settings.api_prefix)
app.include_router(schedules_router, prefix=settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time()
    response = await call_next(request)
    duration_ms = (time() - start) * 1000
    logger.info(
        "http.request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    return response


if settings.enable_metrics:
    Instrumentator(namespace=settings.metrics_namespace).instrument(app).expose(
        app,
        include_in_schema=False,
        tags=["metrics"],
        endpoint=settings.metrics_endpoint,
    )


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
