import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.conversation import Conversation
from app.db.models.message import Message

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Conversation).order_by(Conversation.id.desc()).limit(10))
        convos = result.scalars().all()
        for c in convos:
            msgs = await session.execute(select(Message).where(Message.conversation_id == c.id))
            print(f'ID: {c.id}, Title: {c.title}, Pinned: {c.is_pinned}, Messages count: {len(list(msgs.scalars().all()))}')

asyncio.run(check())
