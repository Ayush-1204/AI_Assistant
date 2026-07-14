from app.routers.auth import router as auth_router
from app.routers.document import router as document_router
from app.routers.health import router as health_router
from app.routers.users import router as users_router

from .auth import router as auth_router
from .conversation import router as conversation_router
from .skills import router as skills_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "health_router",
    "users_router",
    "conversation_router",
    "document_router",
    "skills_router",
]