from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    print("===================================")
    print("Second Brain API Starting...")
    print("===================================")

    yield

    print("===================================")
    print("Second Brain API Stopped.")
    print("===================================")