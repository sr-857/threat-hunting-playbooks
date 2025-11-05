from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.playbooks import router as playbooks_router
from app.api.routers.schedules import router as schedules_router
from app.services.bootstrap import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db(seed=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(playbooks_router, prefix=settings.api_prefix)
app.include_router(schedules_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
