from fastapi import APIRouter, Depends

from app.dependencies import (
    get_ai_service,
    get_current_user,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai import AIService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    response = await service.chat(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        prompt=request.message,
    )

    return ChatResponse(
        response=response,
    )