from dataclasses import dataclass

from src.config import Settings
from src.core.constants import DecisionType
from src.repositories.embedding_repository import EmbeddingRepository, SearchHit


@dataclass
class RetrievalResult:
    """Result from retrieval service."""

    hits: list[SearchHit]
    confidence: float
    decision: DecisionType


class RetrievalService:
    """Service for semantic retrieval operations."""

    def __init__(
        self,
        embedding_repo: EmbeddingRepository,
        settings: Settings,
    ):
        self._embedding_repo = embedding_repo
        self._settings = settings

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        dish_id: int | None = None,
    ) -> RetrievalResult:
        """Search for similar chunks and calculate confidence."""
        hits = self._embedding_repo.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            dish_id=dish_id,
        )

        confidence = max([h.score for h in hits], default=0.0)
        decision = self._calculate_decision(confidence, has_hits=bool(hits))

        return RetrievalResult(
            hits=hits,
            confidence=confidence,
            decision=decision,
        )

    def _calculate_decision(self, confidence: float, has_hits: bool) -> DecisionType:
        """Calculate decision based on confidence and hits."""
        if not has_hits:
            return DecisionType.DISCLAIMER

        if confidence >= self._settings.confidence_answer_threshold:
            return DecisionType.ANSWER

        if confidence >= self._settings.confidence_soft_threshold:
            return DecisionType.SOFT_DISCLAIMER

        return DecisionType.DISCLAIMER
