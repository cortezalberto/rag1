"""Tests for TextService."""

import pytest

from src.services import TextService
from src.config import Settings


class TestTextServiceNormalize:
    """Tests for TextService.normalize method."""

    def test_normalize_removes_non_breaking_spaces(self, text_service: TextService):
        """Should replace non-breaking spaces with regular spaces."""
        text = "hello\u00a0world"
        result = text_service.normalize(text)
        assert result == "hello world"

    def test_normalize_collapses_multiple_spaces(self, text_service: TextService):
        """Should collapse multiple spaces into one."""
        text = "hello    world"
        result = text_service.normalize(text)
        assert result == "hello world"

    def test_normalize_collapses_multiple_newlines(self, text_service: TextService):
        """Should collapse 3+ newlines into 2."""
        text = "hello\n\n\n\nworld"
        result = text_service.normalize(text)
        assert result == "hello\n\nworld"

    def test_normalize_strips_whitespace(self, text_service: TextService):
        """Should strip leading and trailing whitespace."""
        text = "  hello world  "
        result = text_service.normalize(text)
        assert result == "hello world"


class TestTextServiceChunk:
    """Tests for TextService.chunk method."""

    def test_chunk_empty_text(self, text_service: TextService):
        """Should return empty list for empty text."""
        result = text_service.chunk("")
        assert result == []

    def test_chunk_short_text(self, text_service: TextService):
        """Should return single chunk for short text."""
        text = "Short text"
        result = text_service.chunk(text)
        assert len(result) == 1
        assert result[0] == "Short text"

    def test_chunk_creates_overlapping_chunks(self, test_settings: Settings):
        """Should create overlapping chunks for long text."""
        # Create service with small chunk size for testing
        test_settings.chunk_size = 100
        test_settings.chunk_overlap = 20
        service = TextService(test_settings)

        text = "A" * 200  # Long enough to require multiple chunks
        result = service.chunk(text)

        assert len(result) > 1


class TestTextServiceAllergyQuery:
    """Tests for TextService.is_allergy_query method."""

    @pytest.mark.parametrize(
        "query",
        [
            "Tiene gluten?",
            "Es apto para celíacos?",
            "Contiene maní?",
            "Tiene lácteos?",
            "Puede contener trazas de sésamo?",
            "Es sin TACC?",
            "Tiene huevo?",
            "Contiene soja?",
        ],
    )
    def test_detects_allergy_queries(self, text_service: TextService, query: str):
        """Should detect allergy-related queries."""
        assert text_service.is_allergy_query(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "Cuánto cuesta?",
            "Qué ingredientes tiene?",
            "Es picante?",
            "Viene con papas?",
        ],
    )
    def test_non_allergy_queries(self, text_service: TextService, query: str):
        """Should not flag non-allergy queries."""
        assert text_service.is_allergy_query(query) is False


class TestTextServicePreview:
    """Tests for TextService.truncate_for_preview method."""

    def test_truncates_long_text(self, text_service: TextService):
        """Should truncate text longer than preview chars."""
        text = "A" * 500
        result = text_service.truncate_for_preview(text)
        assert len(result) <= text_service._settings.source_preview_chars

    def test_replaces_newlines(self, text_service: TextService):
        """Should replace newlines with spaces."""
        text = "hello\nworld"
        result = text_service.truncate_for_preview(text)
        assert "\n" not in result
