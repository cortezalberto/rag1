from typing import NamedTuple

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from src.models.entities import KBChunk, KBEmbedding


class SearchHit(NamedTuple):
    """Result from semantic search."""

    chunk_id: int
    content: str
    score: float


class EmbeddingRepository:
    """Repository for KBEmbedding entity operations."""

    def __init__(self, db: Session):
        self._db = db

    def count(self) -> int:
        """Count total embeddings."""
        return self._db.scalar(select(func.count()).select_from(KBEmbedding)) or 0

    def create(self, chunk_id: int, embedding: list[float]) -> KBEmbedding:
        """Create a new embedding for a chunk."""
        emb = KBEmbedding(chunk_id=chunk_id, embedding=embedding)
        self._db.add(emb)
        self._db.flush()
        return emb

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int,
        dish_id: int | None = None,
    ) -> list[SearchHit]:
        """Search for similar chunks using cosine distance."""
        stmt = (
            select(
                KBChunk.id,
                KBChunk.content,
                KBEmbedding.embedding.cosine_distance(query_embedding).label("dist"),
            )
            .join(KBEmbedding, KBEmbedding.chunk_id == KBChunk.id)
        )

        if dish_id is not None:
            stmt = stmt.where(KBChunk.dish_id == dish_id)

        stmt = stmt.order_by(text("dist ASC")).limit(top_k)
        rows = self._db.execute(stmt).all()

        hits = []
        for chunk_id, content, dist in rows:
            dist_f = float(dist) if dist is not None else 1.0
            score = max(0.0, 1.0 - dist_f)
            hits.append(SearchHit(chunk_id=int(chunk_id), content=content, score=score))

        return hits

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()
