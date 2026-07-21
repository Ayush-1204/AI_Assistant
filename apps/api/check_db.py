import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Conversation
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Conversation))
        convos = result.scalars().all()
        for c in convos:
            print(f"ID: {c.id}, Pinned: {c.is_pinned}, Title: {c.title}")
            
if __name__ == "__main__":
    asyncio.run(check())
