"""
One-time migration: make oauth_states.user_id nullable for Google sign-in flow.
Run: python migrate_oauth_state.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def run():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.sql import text
    from app.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE oauth_states ALTER COLUMN user_id DROP NOT NULL"
        ))
        print("✅ Done: oauth_states.user_id is now nullable")
    await engine.dispose()

asyncio.run(run())
