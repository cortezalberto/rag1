from pydantic import BaseModel, Field

from src.config import get_settings


settings = get_settings()


class ChatIn(BaseModel):
    """Request schema for chat endpoint."""

    question: str = Field(..., min_length=1)
    dish_id: int | None = None
    top_k: int = Field(default=settings.top_k_default, ge=1, le=12)


class SourceOut(BaseModel):
    """Source chunk information in chat response."""

    chunk_id: int
    score: float
    preview: str


class ChatOut(BaseModel):
    """Response schema for chat endpoint."""

    answer: str
    decision: str
    confidence: float
    sources: list[SourceOut]
    trace_id: int
