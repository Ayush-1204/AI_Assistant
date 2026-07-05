from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base
import enum

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.reminder import Reminder

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reminder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminders.id", ondelete="SET NULL")) # Linked if spawned by reminder
    
    execution_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True)) # Actual time executed
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True) # Expected time to run
    planner_execution_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[JobStatus] = mapped_column(String, default=JobStatus.PENDING)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship("User")
    reminder: Mapped[Optional["Reminder"]] = relationship("Reminder")
