from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models.entities import KBChunk, KBEmbedding


class ChunkRepository:
    """Repository for KBChunk entity operations."""

    def __init__(self, db: Session):
        self._db = db

    def get_unindexed(self) -> list[KBChunk]:
        """Get chunks that don't have embeddings yet."""
        stmt = (
            select(KBChunk)
            .outerjoin(KBEmbedding, KBEmbedding.chunk_id == KBChunk.id)
            .where(KBEmbedding.chunk_id.is_(None))
            .order_by(KBChunk.id)
        )
        return list(self._db.execute(stmt).scalars().all())

    def count(self) -> int:
        """Count total chunks."""
        return self._db.scalar(select(func.count()).select_from(KBChunk)) or 0

    def create(self, chunk: KBChunk) -> KBChunk:
        """Create a new chunk."""
        self._db.add(chunk)
        self._db.flush()
        return chunk

    def create_for_dish(
        self,
        dish_id: int,
        chunks_content: list[str],
        metadata: dict | None = None,
    ) -> list[KBChunk]:
        """Create chunks for a dish from content list."""
        chunks = []
        for idx, content in enumerate(chunks_content, start=1):
            chunk = KBChunk(
                dish_id=dish_id,
                chunk_index=idx,
                content=content,
                meta_data=metadata or {"source": "seed", "type": "ficha_plato"},
            )
            self._db.add(chunk)
            chunks.append(chunk)
        self._db.flush()
        return chunks

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()
