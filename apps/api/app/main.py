from fastapi import FastAPI

from app.config import get_settings
from app.lifespan import lifespan
from app.routers.health import router as health_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(health_router)