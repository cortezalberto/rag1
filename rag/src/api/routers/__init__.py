from .health import router as health_router
from .dishes import router as dishes_router
from .chat import router as chat_router
from .admin import router as admin_router

__all__ = [
    "health_router",
    "dishes_router",
    "chat_router",
    "admin_router",
]
