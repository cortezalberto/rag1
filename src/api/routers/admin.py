from fastapi import APIRouter, HTTPException

from src.schemas import SeedResponse, IndexResponse
from src.api.dependencies import (
    SeedServiceDep,
    ChunkRepoDep,
    EmbeddingRepoDep,
    OllamaServiceDep,
)
from src.core.exceptions import OllamaError


router = APIRouter(tags=["admin"])


@router.post("/seed", response_model=SeedResponse)
def seed(seed_service: SeedServiceDep) -> SeedResponse:
    """Seed the database with initial dish data."""
    ok, message = seed_service.seed_dishes()
    return SeedResponse(ok=ok, message=message)


@router.post("/index", response_model=IndexResponse)
async def index_embeddings(
    chunk_repo: ChunkRepoDep,
    embedding_repo: EmbeddingRepoDep,
    ollama_service: OllamaServiceDep,
) -> IndexResponse:
    """Generate embeddings for chunks that don't have them yet."""
    chunks = chunk_repo.get_unindexed()

    if not chunks:
        return IndexResponse(
            ok=True,
            message="No hay chunks pendientes de indexar.",
        )

    try:
        created = 0
        for chunk in chunks:
            embedding = await ollama_service.generate_embedding(chunk.content)
            embedding_repo.create(chunk_id=chunk.id, embedding=embedding)
            created += 1

        embedding_repo.commit()

        return IndexResponse(
            ok=True,
            embeddings_created=created,
        )
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=f"{e.message}: {e.detail or ''}")
