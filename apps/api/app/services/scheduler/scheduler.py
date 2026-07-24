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
        from app.db.session import AsyncSessionLocal
        while self.running:
            try:
                async with AsyncSessionLocal() as session:
                    worker = await self.worker_factory(session)
                    await worker.poll_due_reminders()
                    await worker.process_pending_jobs()
                    await worker.reschedule_completed_cron_jobs()
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
