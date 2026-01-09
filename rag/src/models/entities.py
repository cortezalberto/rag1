from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    BigInteger,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    ARRAY,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class Dish(Base):
    """Restaurant menu dish."""

    __tablename__ = "dish"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    chunks: Mapped[List["KBChunk"]] = relationship(
        back_populates="dish", cascade="all, delete-orphan"
    )


class KBChunk(Base):
    """Knowledge base text chunk from dish descriptions."""

    __tablename__ = "kb_chunk"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dish_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("dish.id", ondelete="CASCADE"), nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    dish: Mapped[Optional[Dish]] = relationship(back_populates="chunks")
    embedding: Mapped[Optional["KBEmbedding"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan", uselist=False
    )


class KBEmbedding(Base):
    """Vector embedding for a knowledge base chunk."""

    __tablename__ = "kb_embedding"

    chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("kb_chunk.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[List[float]] = mapped_column(Vector(768), nullable=False)

    # Relationships
    chunk: Mapped[KBChunk] = relationship(back_populates="embedding")


class ChatTurn(Base):
    """Single turn in a chat conversation."""

    __tablename__ = "chat_turn"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dish_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("dish.id"), nullable=True
    )
    user_text: Mapped[str] = mapped_column(Text, nullable=False)
    bot_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class RagTrace(Base):
    """RAG trace for audit and debugging."""

    __tablename__ = "rag_trace"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    turn_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_turn.id", ondelete="CASCADE"), nullable=False
    )
    used_chunk_ids: Mapped[List[int]] = mapped_column(ARRAY(BigInteger), nullable=False)
    scores: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    confidence: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
