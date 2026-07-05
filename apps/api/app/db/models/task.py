from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=1)
    
    due_date = Column(DateTime(timezone=True), nullable=True)
    recurrence = Column(String(100), nullable=True)
    
    tags = Column(JSONB, default=list)
    project = Column(String(255), nullable=True)

    user = relationship("User")
