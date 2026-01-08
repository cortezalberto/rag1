from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.entities import ChatTurn, RagTrace


class ChatRepository:
    """Repository for ChatTurn and RagTrace entity operations."""

    def __init__(self, db: Session):
        self._db = db

    def create_turn(
        self,
        user_text: str,
        dish_id: int | None = None,
    ) -> ChatTurn:
        """Create a new chat turn."""
        turn = ChatTurn(dish_id=dish_id, user_text=user_text, bot_text=None)
        self._db.add(turn)
        self._db.commit()
        self._db.refresh(turn)
        return turn

    def update_turn_response(self, turn_id: int, bot_text: str) -> None:
        """Update the bot response for a chat turn."""
        self._db.execute(
            text("UPDATE chat_turn SET bot_text = :bot WHERE id = :id"),
            {"bot": bot_text, "id": turn_id},
        )

    def create_trace(
        self,
        turn_id: int,
        used_chunk_ids: list[int],
        scores: list[float],
        confidence: float,
        decision: str,
    ) -> RagTrace:
        """Create a RAG trace record."""
        trace = RagTrace(
            turn_id=turn_id,
            used_chunk_ids=used_chunk_ids or [0],
            scores=[f"{s:.4f}" for s in scores] or ["0.0000"],
            confidence=f"{confidence:.4f}",
            decision=decision,
        )
        self._db.add(trace)
        self._db.commit()
        self._db.refresh(trace)
        return trace

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()
