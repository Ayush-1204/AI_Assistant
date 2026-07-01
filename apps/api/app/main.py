from fastapi import FastAPI

from app.config import get_settings
from app.lifespan import lifespan
from app.routers import (
    auth_router,
    health_router,
    users_router,
    conversation_router,
)
from app.routers.chat import router as chat_router
from app.routers.document import router as document_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(conversation_router)
app.include_router(chat_router)
app.include_router(document_router)