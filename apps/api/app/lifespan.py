from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    print("===================================")
    print("Second Brain API Starting...")
    print("===================================")

    from app.config import get_settings
    from app.dependencies import boot_scheduler
    settings = get_settings()
    
    scheduler = None
    reflection_task = None
    if getattr(settings, "ENABLE_SCHEDULER", False):
        print("Booting Proactive Scheduler daemon...")
        scheduler = boot_scheduler()
        
        from app.dependencies import _router_instance
        from app.services.scheduler.reflection import ReflectionLoop
        print("Booting Daily Reflection Loop...")
        reflection = ReflectionLoop(provider=_router_instance)
        import asyncio
        reflection_task = asyncio.create_task(reflection.start_loop())

    yield

    if scheduler:
        print("Shutting down Proactive Scheduler daemon...")
        scheduler.stop()
    
    if reflection_task:
        print("Shutting down Reflection Loop...")
        reflection_task.cancel()

    print("===================================")
    print("Second Brain API Stopped.")
    print("===================================")