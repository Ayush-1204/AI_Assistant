import logging
import asyncio
from app.db.models.scheduled_job import ScheduledJob, JobStatus
from app.services.ai.planner.planner import Planner
from app.services.ai.planner.executor import AgentExecutor
from app.services.notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AgentDispatcher:
    def __init__(self, planner: Planner | None, executor: AgentExecutor | None, notification_service: NotificationService, db):
        self.planner = planner
        self.executor = executor
        self.notification_service = notification_service
        self.db = db

    async def execute_job(self, job_id: int) -> None:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import select
        
        logger.info(f"[Dispatcher] Starting execution for ScheduledJob {job_id}")
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
                job = result.scalar_one_or_none()
                if not job:
                    logger.error(f"[Dispatcher] Job ID {job_id} not found in DB")
                    return
                    
                # Re-instantiate notification bounds with the secure async thread context
                from app.services.notifications.notification_service import NotificationService
                from app.services.notifications.providers.database_provider import DatabaseNotificationProvider
                from app.services.notifications.providers.email_provider import EmailNotificationProvider
                from app.services.notifications.providers.push_provider import PushNotificationProvider
                
                notif_svc = NotificationService([
                    DatabaseNotificationProvider(session),
                    EmailNotificationProvider(),
                    PushNotificationProvider(session)
                ])
                
                await notif_svc.notify(
                     job.user_id,  # type: ignore
                     title="Reminder Due", 
                     message=f"Your scheduled event has triggered for Job {job.id}.",
                     type="REMINDER", priority=1
                )
                
                job.status = JobStatus.COMPLETED  # type: ignore
                await session.commit()
                
            except Exception as e:
                logger.error(f"[Dispatcher] Job {job_id} failed: {e}")
                # We attempt recovery update
                try:
                    result = await session.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
                    job = result.scalar_one_or_none()
                    if job:
                        job.status = JobStatus.FAILED  # type: ignore
                        job.failure_reason = str(e)  # type: ignore
                        await session.commit()
                except Exception as inner_e:
                    logger.error(f"[Dispatcher] Recovery save failed: {inner_e}")
