"""
Menu RAG - FastAPI Application Entry Point

A Retrieval-Augmented Generation system for restaurant menu queries
with emphasis on allergen information and food safety.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.models.database import init_db
from src.api.routers import (
    health_router,
    dishes_router,
    chat_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown (nothing to do)


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Menu RAG MVP",
        description="FastAPI + PostgreSQL + pgvector + Ollama",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(dishes_router)
    app.include_router(chat_router)
    app.include_router(admin_router)

    return app


# Create application instance
app = create_app()
