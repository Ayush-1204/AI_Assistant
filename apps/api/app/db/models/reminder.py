from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User

class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    reminder_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    snooze_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User")
