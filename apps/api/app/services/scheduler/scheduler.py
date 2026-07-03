import asyncio
import logging
from app.config import settings

class BackgroundScheduler:
    def __init__(self, worker_factory):
        self.worker_factory = worker_factory
        self.interval = getattr(settings, "SCHEDULER_INTERVAL_SECONDS", 10)
        self.running = False
        self.task = None

    async def _loop(self):
        while self.running:
            try:
                # We need a new session per tick to avoid transaction leaks
                worker = await self.worker_factory()
                await worker.poll_due_reminders()
                await worker.process_pending_jobs()
            except Exception as e:
                logging.error(f"Scheduler loop error: {e}")
            await asyncio.sleep(self.interval)

    def start(self):
        self.running = True
        self.task = asyncio.create_task(self._loop())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
