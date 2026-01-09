class PromptService:
    """Service for building LLM prompts."""

    SYSTEM_PROMPT_BASE = (
        "Sos un asistente de carta gastronómica.\n"
        "REGLA CRÍTICA: NO inventes ingredientes ni alérgenos.\n"
        "Solo afirmes 'contiene X' si aparece explícitamente en la EVIDENCIA.\n"
        "Si falta evidencia o no está claro, decí: 'No puedo confirmarlo con la información disponible' "
        "y sugerí verificar con el personal.\n"
        "Respondé en español, claro, directo, sin marketing.\n"
        "Formato:\n"
        "1) Resumen (1-2 líneas)\n"
        "2) Ingredientes (si hay evidencia)\n"
        "3) Alérgenos (si hay evidencia; si no, 'No confirmado')\n"
        "4) Adaptaciones posibles (si hay evidencia)\n"
        "5) Nota de seguridad (si aplica)\n"
    )

    ALLERGY_MODE_ADDITION = (
        "\nMODO ALERGIA ACTIVO:\n"
        "- Sé extremadamente conservador.\n"
        "- Si hay duda o falta evidencia, marcá 'No confirmado' y recomendá verificación.\n"
    )

    USER_PROMPT_TEMPLATE = (
        "CONSULTA DEL COMENSAL:\n{question}\n\n"
        "EVIDENCIA (usar solo esto como fuente):\n{evidence}\n\n"
        "IMPORTANTE:\n"
        "- Si la evidencia es 'SIN_EVIDENCIA' o no menciona el punto consultado, respondé con 'No puedo confirmarlo'.\n"
        "- Al final agregá: Fuentes: [chunk:ID] ... (solo si usaste evidencia)\n"
    )

    NO_EVIDENCE_RESPONSE = (
        "No puedo confirmarlo con la información disponible en las fichas cargadas.\n\n"
        "Si me decís el nombre exacto del plato o cargás la ficha correspondiente, lo reviso. "
        "Por seguridad (especialmente por alérgenos), verificá con el personal."
    )

    SOFT_DISCLAIMER_SUFFIX = (
        "\n\nNota: la evidencia recuperada es parcial; si es por alergias/intolerancias, "
        "confirmá con el personal."
    )

    def build_system_prompt(self, allergy_mode: bool = False) -> str:
        """Build the system prompt for the LLM."""
        prompt = self.SYSTEM_PROMPT_BASE
        if allergy_mode:
            prompt += self.ALLERGY_MODE_ADDITION
        return prompt

    def build_user_prompt(
        self,
        question: str,
        evidence_chunks: list[tuple[int, str]],
    ) -> str:
        """Build the user prompt with question and evidence."""
        if evidence_chunks:
            evidence_block = "\n\n".join(
                f"[chunk:{chunk_id}] {content}"
                for chunk_id, content in evidence_chunks
            )
        else:
            evidence_block = "SIN_EVIDENCIA"

        return self.USER_PROMPT_TEMPLATE.format(
            question=question,
            evidence=evidence_block,
        )

    def get_no_evidence_response(self) -> str:
        """Get the response for when there's no evidence."""
        return self.NO_EVIDENCE_RESPONSE

    def add_soft_disclaimer(self, answer: str) -> str:
        """Add soft disclaimer to answer."""
        return answer + self.SOFT_DISCLAIMER_SUFFIX
