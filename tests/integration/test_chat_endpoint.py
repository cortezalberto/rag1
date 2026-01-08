"""Integration tests for chat endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


class TestChatEndpoint:
    """Integration tests for /chat endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        from app import app
        return TestClient(app)

    @pytest.mark.skip(reason="Requires database and Ollama running")
    def test_chat_endpoint_returns_response(self, client: TestClient):
        """Should return chat response with all required fields."""
        response = client.post(
            "/chat",
            json={"question": "Tiene gluten?", "top_k": 3},
        )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "decision" in data
        assert "confidence" in data
        assert "sources" in data
        assert "trace_id" in data

    @pytest.mark.skip(reason="Requires database and Ollama running")
    def test_chat_endpoint_validates_question(self, client: TestClient):
        """Should reject empty question."""
        response = client.post(
            "/chat",
            json={"question": "", "top_k": 3},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Requires database and Ollama running")
    def test_chat_endpoint_validates_top_k(self, client: TestClient):
        """Should reject invalid top_k values."""
        response = client.post(
            "/chat",
            json={"question": "Test", "top_k": 100},
        )

        assert response.status_code == 422  # Validation error
