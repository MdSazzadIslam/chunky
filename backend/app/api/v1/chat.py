from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service, get_user_id
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user_id: str = Depends(get_user_id),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return service.answer(
        user_id=user_id,
        question=payload.question,
        document_id=payload.document_id,
    )
