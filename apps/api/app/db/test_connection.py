from sqlalchemy import text

from app.db.session import engine


async def test_connection():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT version();"))
        print(result.scalar())