from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str | None = None


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime