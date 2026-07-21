from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.schemas.message import MessageResponse


class ConversationBase(BaseModel):
    title: str
    is_pinned: bool = False


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []