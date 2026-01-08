from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@127.0.0.1:5434/menu_rag",
        alias="DATABASE_URL"
    )

    # Ollama
    ollama_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_URL"
    )
    embed_model: str = Field(
        default="nomic-embed-text",
        alias="EMBED_MODEL"
    )
    chat_model: str = Field(
        default="llama3.2:1b",
        alias="CHAT_MODEL"
    )

    # RAG Configuration
    top_k_default: int = Field(default=6)
    chunk_size: int = Field(default=1200)
    chunk_overlap: int = Field(default=200)

    # Confidence Thresholds
    confidence_answer_threshold: float = Field(default=0.78)
    confidence_soft_threshold: float = Field(default=0.60)

    # Timeouts (seconds)
    ollama_embed_timeout: int = Field(default=60)
    ollama_chat_timeout: int = Field(default=300)
    ollama_health_timeout: int = Field(default=3)

    # Preview
    source_preview_chars: int = Field(default=220)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
