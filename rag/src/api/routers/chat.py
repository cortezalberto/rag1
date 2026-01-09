from fastapi import APIRouter, HTTPException

from src.schemas import ChatIn, ChatOut
from src.api.dependencies import ChatServiceDep
from src.services.chat_service import ChatRequest
from src.core.exceptions import OllamaError


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatOut)
async def chat(
    req: ChatIn,
    chat_service: ChatServiceDep,
) -> ChatOut:
    """Process a chat query through the RAG pipeline."""
    try:
        request = ChatRequest(
            question=req.question,
            dish_id=req.dish_id,
            top_k=req.top_k,
        )
        return await chat_service.process_query(request)
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=f"{e.message}: {e.detail or ''}")
