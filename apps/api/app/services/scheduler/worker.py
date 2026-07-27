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
            # Check if job already exists to avoid duplicates
            job_check = await self.db.execute(
                select(ScheduledJob).where(ScheduledJob.reminder_id == reminder.id)
            )
            if job_check.scalar_one_or_none() is None:
                logger.info(f"Detected due reminder {reminder.id}: {reminder.title}")
                job = ScheduledJob(
                    user_id=reminder.user_id,
                    reminder_id=reminder.id,
                    scheduled_time=reminder.reminder_time,
                    status=JobStatus.PENDING
                )
                self.db.add(job)
            reminder.is_completed = True
        
        if due_reminders:
            await self.db.commit()

    async def process_pending_jobs(self) -> None:
        now = datetime.now(timezone.utc)
        # We need an explicit transaction and locking
        result = await self.db.execute(
            select(ScheduledJob).where(
                ScheduledJob.status == JobStatus.PENDING,
                ScheduledJob.scheduled_time <= now,
                ScheduledJob.is_enabled == True,  # noqa: E712
            ).with_for_update(skip_locked=True)
        )
        jobs = result.scalars().all()
        
        for job in jobs:
            job.status = JobStatus.RUNNING
            job.execution_time = now
            
        if jobs:
            await self.db.commit()
            
            for job in jobs:
                asyncio.create_task(self.dispatcher.execute_job(job.id))

    async def reschedule_completed_cron_jobs(self) -> None:
        """After a cron job completes, compute next_run_at and reset to PENDING."""
        try:
            from croniter import croniter  # type: ignore
        except ImportError:
            return
        
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(ScheduledJob).where(
                ScheduledJob.status == JobStatus.COMPLETED,
                ScheduledJob.cron_expression != None,  # noqa: E711
                ScheduledJob.is_user_defined == True,  # noqa: E712
            )
        )
        completed_cron_jobs = result.scalars().all()
        
        for job in completed_cron_jobs:
            try:
                cron = croniter(job.cron_expression, now)
                next_time = cron.get_next(datetime)
                
                if job.end_repeat_at and next_time > job.end_repeat_at:
                    logger.info(f"[Worker] Cron job {job.id} reached end_repeat_at. Leaving as COMPLETED.")
                    job.is_enabled = False
                    continue

                job.scheduled_time = next_time
                job.next_run_at = next_time
                job.status = JobStatus.PENDING
                job.failure_reason = None
                logger.info(f"[Worker] Rescheduled cron job {job.id} -> next run at {next_time}")
            except Exception as e:
                logger.error(f"[Worker] Failed to reschedule job {job.id}: {e}")
        
        if completed_cron_jobs:
            await self.db.commit()
