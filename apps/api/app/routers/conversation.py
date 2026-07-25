from fastapi import APIRouter, Depends, Response, status

from app.db.models.user import User
from app.dependencies import (
    get_conversation_service,
    get_message_service,
    get_current_user,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    ConversationDetailResponse
)
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from pydantic import BaseModel

class TruncateRequest(BaseModel):
    from_index: int


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(
        get_conversation_service,
    ),
):
    return await service.create(
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(
        get_conversation_service,
    ),
):
    return await service.list_by_user(
        current_user.id,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(
        get_conversation_service,
    ),
):
    return await service.get_by_id(
        conversation_id,
        current_user.id,
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(
        get_conversation_service,
    ),
):
    return await service.update(
        conversation_id,
        current_user.id,
        data,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(
        get_conversation_service,
    ),
):
    await service.delete(
        conversation_id,
        current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "/{conversation_id}/truncate",
    status_code=status.HTTP_200_OK,
)
async def truncate_conversation(
    conversation_id: int,
    data: TruncateRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
    message_service: MessageService = Depends(get_message_service),
):
    # Verify the conversation belongs to the user
    await service.get_by_id(conversation_id, current_user.id)
    # Truncate messages
    await message_service.delete_messages_from_index(conversation_id, data.from_index)
    return {"status": "ok"}