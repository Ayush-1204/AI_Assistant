import asyncio

from app.db.test_connection import test_connection


asyncio.run(test_connection())