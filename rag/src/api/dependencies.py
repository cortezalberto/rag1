from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from src.config import Settings, get_settings as _get_settings
from src.models.database import SessionLocal
from src.repositories import (
    DishRepository,
    ChunkRepository,
    EmbeddingRepository,
    ChatRepository,
)
from src.services import (
    OllamaService,
    TextService,
    PromptService,
    RetrievalService,
    ChatService,
    SeedService,
)


def get_settings() -> Settings:
    """Get application settings."""
    return _get_settings()


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Type aliases for cleaner dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]


def get_ollama_service(settings: SettingsDep) -> OllamaService:
    """Get Ollama service instance."""
    return OllamaService(settings)


def get_text_service(settings: SettingsDep) -> TextService:
    """Get text service instance."""
    return TextService(settings)


def get_prompt_service() -> PromptService:
    """Get prompt service instance."""
    return PromptService()


# Repository dependencies
def get_dish_repo(db: DbDep) -> DishRepository:
    """Get dish repository instance."""
    return DishRepository(db)


def get_chunk_repo(db: DbDep) -> ChunkRepository:
    """Get chunk repository instance."""
    return ChunkRepository(db)


def get_embedding_repo(db: DbDep) -> EmbeddingRepository:
    """Get embedding repository instance."""
    return EmbeddingRepository(db)


def get_chat_repo(db: DbDep) -> ChatRepository:
    """Get chat repository instance."""
    return ChatRepository(db)


# Service dependencies with type aliases
OllamaServiceDep = Annotated[OllamaService, Depends(get_ollama_service)]
TextServiceDep = Annotated[TextService, Depends(get_text_service)]
PromptServiceDep = Annotated[PromptService, Depends(get_prompt_service)]
DishRepoDep = Annotated[DishRepository, Depends(get_dish_repo)]
ChunkRepoDep = Annotated[ChunkRepository, Depends(get_chunk_repo)]
EmbeddingRepoDep = Annotated[EmbeddingRepository, Depends(get_embedding_repo)]
ChatRepoDep = Annotated[ChatRepository, Depends(get_chat_repo)]


def get_retrieval_service(
    embedding_repo: EmbeddingRepoDep,
    settings: SettingsDep,
) -> RetrievalService:
    """Get retrieval service instance."""
    return RetrievalService(embedding_repo, settings)


def get_chat_service(
    ollama_service: OllamaServiceDep,
    text_service: TextServiceDep,
    prompt_service: PromptServiceDep,
    chat_repo: ChatRepoDep,
    embedding_repo: EmbeddingRepoDep,
    settings: SettingsDep,
) -> ChatService:
    """Get chat service instance."""
    retrieval_service = RetrievalService(embedding_repo, settings)
    return ChatService(
        ollama_service=ollama_service,
        text_service=text_service,
        prompt_service=prompt_service,
        retrieval_service=retrieval_service,
        chat_repo=chat_repo,
        embedding_repo=embedding_repo,
        settings=settings,
    )


def get_seed_service(
    dish_repo: DishRepoDep,
    chunk_repo: ChunkRepoDep,
    text_service: TextServiceDep,
    settings: SettingsDep,
) -> SeedService:
    """Get seed service instance."""
    return SeedService(
        dish_repo=dish_repo,
        chunk_repo=chunk_repo,
        text_service=text_service,
        settings=settings,
    )


# Composite type aliases for routers
RetrievalServiceDep = Annotated[RetrievalService, Depends(get_retrieval_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
SeedServiceDep = Annotated[SeedService, Depends(get_seed_service)]
