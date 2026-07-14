
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

person_memory_association = Table(
    "person_memory",
    Base.metadata,
    Column("person_id", ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
    Column("memory_id", ForeignKey("memories.id", ondelete="CASCADE"), primary_key=True)
)

person_note_association = Table(
    "person_note",
    Base.metadata,
    Column("person_id", ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
    Column("note_id", ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
)

class Person(Base):
    __tablename__ = "people"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    last_mentioned: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", back_populates="people")
    memories = relationship("Memory", secondary=person_memory_association, back_populates="people")
    notes = relationship("Note", secondary=person_note_association, back_populates="people")
