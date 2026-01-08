from fastapi import APIRouter

from src.schemas import HealthResponse
from src.api.dependencies import (
    SettingsDep,
    OllamaServiceDep,
    DishRepoDep,
    ChunkRepoDep,
    EmbeddingRepoDep,
)


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    settings: SettingsDep,
    ollama_service: OllamaServiceDep,
    dish_repo: DishRepoDep,
    chunk_repo: ChunkRepoDep,
    embedding_repo: EmbeddingRepoDep,
) -> HealthResponse:
    """Check system health status."""
    ollama_reachable = await ollama_service.is_reachable()

    return HealthResponse(
        ok=True,
        ollama_reachable=ollama_reachable,
        embed_model=settings.embed_model,
        chat_model=settings.chat_model,
        dishes=dish_repo.count(),
        chunks=chunk_repo.count(),
        embeddings=embedding_repo.count(),
    )
