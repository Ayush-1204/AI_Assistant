from datetime import datetime

from pydantic import BaseModel


class ConversationSummary(BaseModel):
    id: int
    title: str
    last_message: str | None
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }