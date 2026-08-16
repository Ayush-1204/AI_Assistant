import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models.document import Document
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        docs = (await db.execute(select(Document).order_by(Document.id.desc()).limit(1))).scalars().all()
        if docs:
            d = docs[0]
            print(f"ID: {d.id}")
            print(f"File: {d.original_filename}")
            print(f"Path: {d.storage_path}")
            print(f"MIME: {d.mime_type}")
            print(f"Status: {d.status}")
        else:
            print("No docs")

asyncio.run(run())
