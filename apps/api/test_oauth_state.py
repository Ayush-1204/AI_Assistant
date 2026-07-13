import asyncio

from app.db.session import AsyncSessionLocal
from app.repositories.oauth_state_repository import OAuthStateRepository


async def test():
    async with AsyncSessionLocal() as db:
        try:
            repo = OAuthStateRepository(db)
            state = await repo.create_state(1)
            print("SUCCESS:", state)
        except Exception:
            with open("test_out.txt", "w") as f:
                import traceback
                traceback.print_exc(file=f)

if __name__ == "__main__":
    asyncio.run(test())
