from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    print("===================================")
    print("Second Brain API Starting...")
    print("===================================")

    from app.dependencies import boot_scheduler
    from app.config import get_settings
    settings = get_settings()
    
    scheduler = None
    if getattr(settings, "ENABLE_SCHEDULER", False):
        print("Booting Proactive Scheduler daemon...")
        scheduler = boot_scheduler()

    yield

    if scheduler:
        print("Shutting down Proactive Scheduler daemon...")
        scheduler.stop()

    print("===================================")
    print("Second Brain API Stopped.")
    print("===================================")