import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.reminder import Reminder
from app.db.models.scheduled_job import JobStatus, ScheduledJob
from app.services.scheduler.dispatcher import AgentDispatcher

logger = logging.getLogger(__name__)

class SchedulerWorker:
    def __init__(self, db: AsyncSession, dispatcher: AgentDispatcher):
        self.db = db
        self.dispatcher = dispatcher

    async def poll_due_reminders(self) -> None:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Reminder).where(Reminder.reminder_time <= now, Reminder.is_completed == False)
        )
        due_reminders = result.scalars().all()
        
        for reminder in due_reminders:
            logger.info(f"Detected due reminder {reminder.id}: {reminder.title}")
            job = ScheduledJob(
                user_id=reminder.user_id,
                reminder_id=reminder.id,
                scheduled_time=reminder.reminder_time,
                status=JobStatus.PENDING
            )
            self.db.add(job)
            reminder.is_completed = True
            await self.db.commit()

    async def process_pending_jobs(self) -> None:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(ScheduledJob).where(ScheduledJob.status == JobStatus.PENDING, ScheduledJob.scheduled_time <= now)
        )
        jobs = result.scalars().all()
        
        for job in jobs:
            job.status = JobStatus.RUNNING
            job.execution_time = now
            await self.db.commit()
            
            asyncio.create_task(self.dispatcher.execute_job(job.id))
