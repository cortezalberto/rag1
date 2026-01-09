from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from src.config import get_settings
from .entities import Base


settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database: create extension, tables, and indexes."""
    # 1) Ensure pgvector extension exists
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    # 2) Create all tables
    Base.metadata.create_all(engine)

    # 3) Create indexes
    with engine.begin() as conn:
        # Index for dish_id lookup
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS kb_chunk_dish_idx ON kb_chunk(dish_id);")
        )
        # HNSW index for vector similarity search
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS kb_embedding_hnsw "
                    "ON kb_embedding USING hnsw (embedding vector_cosine_ops);"
                )
            )
        except Exception:
            # Index might already exist or not be supported
            pass
