from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.routers.debug import router as debug_router
from app.routers.debug_router import router as debug_router2
from app.routers.notes import router as notes_router
from app.routers.tasks import router as tasks_router
from app.routers.reminders import router as reminders_router
from app.routers.devices import router as devices_router
from app.routers.voice import router as voice_router
from app.routers.dashboard import router as dashboard_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Allow Flutter Web (any localhost port) to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten this to specific domains in production
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(conversation_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(debug_router)
app.include_router(debug_router2)
app.include_router(notes_router)
app.include_router(tasks_router)
app.include_router(reminders_router)
app.include_router(devices_router)
app.include_router(voice_router)
app.include_router(dashboard_router)