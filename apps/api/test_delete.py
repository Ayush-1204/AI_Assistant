import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Conversation
from app.repositories import ConversationRepository
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        repo = ConversationRepository(session)
        convo = await repo.get_by_id(23)
        if convo:
            print(f"Deleting convo 23: {convo.title}")
            await repo.delete(convo)
            print("Deleted.")

        result = await session.execute(select(Conversation))
        convos = result.scalars().all()
        for c in convos[-5:]:
            print(f"ID: {c.id}, Pinned: {c.is_pinned}, Title: {c.title}")

if __name__ == '__main__':
    asyncio.run(main())
