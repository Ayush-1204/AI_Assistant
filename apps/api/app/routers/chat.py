from fastapi import APIRouter, Depends

from app.dependencies import get_ai_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
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
    service: AIService = Depends(
        get_ai_service,
    ),
):
    response = await service.chat(
        request.message,
    )

    return ChatResponse(
        response=response,
    )