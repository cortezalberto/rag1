"""Tests for PromptService."""

import pytest

from src.services import PromptService


class TestPromptServiceSystemPrompt:
    """Tests for PromptService.build_system_prompt method."""

    def test_base_system_prompt(self, prompt_service: PromptService):
        """Should return base system prompt without allergy mode."""
        result = prompt_service.build_system_prompt(allergy_mode=False)

        assert "asistente de carta gastronómica" in result
        assert "NO inventes ingredientes" in result
        assert "MODO ALERGIA" not in result

    def test_allergy_mode_system_prompt(self, prompt_service: PromptService):
        """Should include allergy mode additions."""
        result = prompt_service.build_system_prompt(allergy_mode=True)

        assert "MODO ALERGIA ACTIVO" in result
        assert "extremadamente conservador" in result


class TestPromptServiceUserPrompt:
    """Tests for PromptService.build_user_prompt method."""

    def test_user_prompt_with_evidence(self, prompt_service: PromptService):
        """Should format user prompt with evidence chunks."""
        question = "Tiene gluten?"
        evidence = [(1, "Contiene gluten"), (2, "Alérgenos: trigo")]

        result = prompt_service.build_user_prompt(question, evidence)

        assert question in result
        assert "[chunk:1]" in result
        assert "[chunk:2]" in result
        assert "Contiene gluten" in result

    def test_user_prompt_without_evidence(self, prompt_service: PromptService):
        """Should show SIN_EVIDENCIA when no evidence provided."""
        question = "Tiene gluten?"
        evidence = []

        result = prompt_service.build_user_prompt(question, evidence)

        assert "SIN_EVIDENCIA" in result


class TestPromptServiceResponses:
    """Tests for PromptService response methods."""

    def test_no_evidence_response(self, prompt_service: PromptService):
        """Should return appropriate no evidence response."""
        result = prompt_service.get_no_evidence_response()

        assert "No puedo confirmarlo" in result
        assert "verificá con el personal" in result

    def test_add_soft_disclaimer(self, prompt_service: PromptService):
        """Should append soft disclaimer to answer."""
        answer = "El plato contiene lácteos."
        result = prompt_service.add_soft_disclaimer(answer)

        assert answer in result
        assert "evidencia recuperada es parcial" in result
