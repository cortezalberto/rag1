from dataclasses import dataclass

from src.config import Settings
from src.core.constants import DecisionType
from src.repositories import ChatRepository, EmbeddingRepository
from src.schemas.chat import ChatOut, SourceOut
from .ollama_service import OllamaService
from .text_service import TextService
from .prompt_service import PromptService
from .retrieval_service import RetrievalService


@dataclass
class ChatRequest:
    """Internal request for chat processing."""

    question: str
    dish_id: int | None
    top_k: int


class ChatService:
    """Service for orchestrating the RAG chat flow."""

    def __init__(
        self,
        ollama_service: OllamaService,
        text_service: TextService,
        prompt_service: PromptService,
        retrieval_service: RetrievalService,
        chat_repo: ChatRepository,
        embedding_repo: EmbeddingRepository,
        settings: Settings,
    ):
        self._ollama = ollama_service
        self._text = text_service
        self._prompt = prompt_service
        self._retrieval = retrieval_service
        self._chat_repo = chat_repo
        self._embedding_repo = embedding_repo
        self._settings = settings

    async def process_query(self, request: ChatRequest) -> ChatOut:
        """Process a chat query through the RAG pipeline."""
        # 1. Normalize and analyze query
        normalized_question = self._text.normalize(request.question)
        is_allergy = self._text.is_allergy_query(normalized_question)

        # 2. Create chat turn
        turn = self._chat_repo.create_turn(
            user_text=normalized_question,
            dish_id=request.dish_id,
        )

        # 3. Generate query embedding
        query_embedding = await self._ollama.generate_embedding(normalized_question)

        # 4. Retrieve similar chunks
        retrieval_result = self._retrieval.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            dish_id=request.dish_id,
        )

        # 5. Generate answer
        answer = await self._generate_answer(
            question=normalized_question,
            hits=retrieval_result.hits,
            decision=retrieval_result.decision,
            is_allergy=is_allergy,
        )

        # 6. Create trace
        trace = self._chat_repo.create_trace(
            turn_id=turn.id,
            used_chunk_ids=[h.chunk_id for h in retrieval_result.hits],
            scores=[h.score for h in retrieval_result.hits],
            confidence=retrieval_result.confidence,
            decision=retrieval_result.decision.value,
        )

        # 7. Update turn with bot response
        self._chat_repo.update_turn_response(turn.id, answer)
        self._chat_repo.commit()

        # 8. Build response
        sources = [
            SourceOut(
                chunk_id=h.chunk_id,
                score=h.score,
                preview=self._text.truncate_for_preview(h.content),
            )
            for h in retrieval_result.hits
        ]

        return ChatOut(
            answer=answer,
            decision=retrieval_result.decision.value,
            confidence=retrieval_result.confidence,
            sources=sources,
            trace_id=trace.id,
        )

    async def _generate_answer(
        self,
        question: str,
        hits: list,
        decision: DecisionType,
        is_allergy: bool,
    ) -> str:
        """Generate answer based on retrieved evidence."""
        # No evidence case
        if decision == DecisionType.DISCLAIMER and not hits:
            return self._prompt.get_no_evidence_response()

        # Build prompts
        system_prompt = self._prompt.build_system_prompt(allergy_mode=is_allergy)
        evidence_chunks = [(h.chunk_id, h.content) for h in hits]
        user_prompt = self._prompt.build_user_prompt(question, evidence_chunks)

        # Generate answer
        answer = await self._ollama.chat(system_prompt, user_prompt)

        # Add soft disclaimer if needed
        if decision == DecisionType.SOFT_DISCLAIMER:
            answer = self._prompt.add_soft_disclaimer(answer)

        return answer
