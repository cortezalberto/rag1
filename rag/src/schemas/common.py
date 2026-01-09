from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response schema for health endpoint."""

    ok: bool
    ollama_reachable: bool
    embed_model: str
    chat_model: str
    dishes: int
    chunks: int
    embeddings: int


class SeedResponse(BaseModel):
    """Response schema for seed endpoint."""

    ok: bool
    message: str


class IndexResponse(BaseModel):
    """Response schema for index endpoint."""

    ok: bool
    message: str | None = None
    embeddings_created: int | None = None
