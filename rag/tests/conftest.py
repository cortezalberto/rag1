"""Pytest fixtures for testing."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.config import Settings
from src.services import OllamaService, TextService, PromptService


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with default values."""
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost:5434/test_db",
        ollama_url="http://localhost:11434",
        embed_model="nomic-embed-text",
        chat_model="llama3.2:1b",
    )


@pytest.fixture
def mock_ollama_service(test_settings: Settings) -> OllamaService:
    """Mocked Ollama service for testing."""
    service = OllamaService(test_settings)

    # Mock the methods
    service.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    service.chat = AsyncMock(return_value="Mocked response")
    service.is_reachable = AsyncMock(return_value=True)

    return service


@pytest.fixture
def text_service(test_settings: Settings) -> TextService:
    """Text service instance for testing."""
    return TextService(test_settings)


@pytest.fixture
def prompt_service() -> PromptService:
    """Prompt service instance for testing."""
    return PromptService()
