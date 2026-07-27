import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.reminder import Reminder
    from app.db.models.user import User

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reminder_id: Mapped[int | None] = mapped_column(ForeignKey("reminders.id", ondelete="SET NULL")) # Linked if spawned by reminder
    
    execution_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)) # Actual time executed
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True) # Expected time to run
    planner_execution_id: Mapped[str | None] = mapped_column(String(255))
    
    cron_expression: Mapped[str | None] = mapped_column(String(50)) # For recurring Celery-beat like schedules 
    recurring_action: Mapped[str | None] = mapped_column(Text) # Explicit agent logic to deploy
    
    # User-facing task fields
    label: Mapped[str | None] = mapped_column(String(255))  # Human-readable name
    is_user_defined: Mapped[bool] = mapped_column(Boolean, default=False)  # True = created by user via UI
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)  # Toggle without deleting
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # Cached next fire time
    end_repeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)) # End date for recurring jobs
    
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[JobStatus] = mapped_column(String, default=JobStatus.PENDING)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship("User")
    reminder: Mapped[Optional["Reminder"]] = relationship("Reminder")

    @property
    def directive(self) -> str | None:
        return self.recurring_action
