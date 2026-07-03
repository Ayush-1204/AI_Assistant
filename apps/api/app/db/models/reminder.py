from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    reminder_time = Column(DateTime(timezone=True), nullable=False)
    is_recurring = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    snooze_count = Column(Integer, default=0)

    user = relationship("User")
