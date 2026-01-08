"""Tests for decision logic (confidence thresholds)."""

import pytest

from src.core.constants import DecisionType
from src.config import Settings
from src.services.retrieval_service import RetrievalService
from src.repositories.embedding_repository import EmbeddingRepository
from unittest.mock import MagicMock


class TestDecisionLogic:
    """Tests for confidence-based decision making."""

    @pytest.fixture
    def retrieval_service(self, test_settings: Settings) -> RetrievalService:
        """Create retrieval service with mocked repository."""
        mock_repo = MagicMock(spec=EmbeddingRepository)
        mock_repo.search_similar.return_value = []
        return RetrievalService(mock_repo, test_settings)

    def test_no_hits_returns_disclaimer(
        self, retrieval_service: RetrievalService
    ):
        """Should return disclaimer when no hits."""
        result = retrieval_service._calculate_decision(
            confidence=0.9, has_hits=False
        )
        assert result == DecisionType.DISCLAIMER

    def test_high_confidence_returns_answer(
        self, retrieval_service: RetrievalService
    ):
        """Should return answer for high confidence."""
        result = retrieval_service._calculate_decision(
            confidence=0.85, has_hits=True
        )
        assert result == DecisionType.ANSWER

    def test_medium_confidence_returns_soft_disclaimer(
        self, retrieval_service: RetrievalService
    ):
        """Should return soft_disclaimer for medium confidence."""
        result = retrieval_service._calculate_decision(
            confidence=0.70, has_hits=True
        )
        assert result == DecisionType.SOFT_DISCLAIMER

    def test_low_confidence_returns_disclaimer(
        self, retrieval_service: RetrievalService
    ):
        """Should return disclaimer for low confidence."""
        result = retrieval_service._calculate_decision(
            confidence=0.50, has_hits=True
        )
        assert result == DecisionType.DISCLAIMER

    def test_threshold_boundary_answer(
        self, retrieval_service: RetrievalService
    ):
        """Should return answer at exactly 0.78 threshold."""
        result = retrieval_service._calculate_decision(
            confidence=0.78, has_hits=True
        )
        assert result == DecisionType.ANSWER

    def test_threshold_boundary_soft_disclaimer(
        self, retrieval_service: RetrievalService
    ):
        """Should return soft_disclaimer at exactly 0.60 threshold."""
        result = retrieval_service._calculate_decision(
            confidence=0.60, has_hits=True
        )
        assert result == DecisionType.SOFT_DISCLAIMER

    def test_just_below_answer_threshold(
        self, retrieval_service: RetrievalService
    ):
        """Should return soft_disclaimer just below answer threshold."""
        result = retrieval_service._calculate_decision(
            confidence=0.77, has_hits=True
        )
        assert result == DecisionType.SOFT_DISCLAIMER

    def test_just_below_soft_threshold(
        self, retrieval_service: RetrievalService
    ):
        """Should return disclaimer just below soft threshold."""
        result = retrieval_service._calculate_decision(
            confidence=0.59, has_hits=True
        )
        assert result == DecisionType.DISCLAIMER
