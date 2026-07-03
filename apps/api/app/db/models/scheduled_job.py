from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True) # Linked if spawned by reminder
    
    execution_time = Column(DateTime(timezone=True), nullable=True) # Actual time executed
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True) # Expected time to run
    planner_execution_id = Column(String(255), nullable=True)
    
    retry_count = Column(Integer, default=0)
    status = Column(String, default=JobStatus.PENDING)
    failure_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    reminder = relationship("Reminder")
