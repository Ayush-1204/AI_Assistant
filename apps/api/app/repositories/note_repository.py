from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.note import Note

class NoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, note: Note) -> Note:
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def get_by_id(self, note_id: int, user_id: int) -> Note | None:
        result = await self.session.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Note]:
        result = await self.session.execute(
            select(Note).where(Note.user_id == user_id).order_by(Note.id.desc())
        )
        return list(result.scalars().all())

    async def update(self, note: Note) -> Note:
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def delete(self, note: Note) -> None:
        await self.session.delete(note)
        await self.session.commit()
