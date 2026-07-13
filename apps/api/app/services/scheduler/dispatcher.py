import logging

from app.db.models.scheduled_job import JobStatus, ScheduledJob
from app.services.ai.planner.executor import AgentExecutor
from app.services.ai.planner.planner import Planner
from app.services.notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AgentDispatcher:
    def __init__(self, planner: Planner | None, executor: AgentExecutor | None, notification_service: NotificationService, db):
        self.planner = planner
        self.executor = executor
        self.notification_service = notification_service
        self.db = db

    async def execute_job(self, job_id: int) -> None:
        from sqlalchemy import select

        from app.db.session import AsyncSessionLocal
        
        logger.info(f"[Dispatcher] Starting execution for ScheduledJob {job_id}")
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
                job = result.scalar_one_or_none()
                if not job:
                    logger.error(f"[Dispatcher] Job ID {job_id} not found in DB")
                    return
                    
                if job.recurring_action:
                    logger.info(f"[Dispatcher] Spawning autonomous Chronos Swarm job for {job_id}...")
                    import typing

                    from app.dependencies import _router_instance
                    from app.services.ai.planner.agents.swarm.agents import (
                        SwarmAgent,
                        router_agent,
                    )
                    from app.services.ai.planner.agents.swarm.swarm import SwarmOrchestrator
                    from app.services.ai.providers.router import ProviderRouter
                    
                    router = typing.cast(ProviderRouter, _router_instance)
                    swarm = SwarmOrchestrator(router)
                    
                    cron_agent = SwarmAgent(
                        name="ChronosDaemon",
                        instructions=f"You are a backend daemon tracking autonomous execution. Task Directive: {job.recurring_action}",
                        tools=router_agent.tools
                    )
                    result_text = await swarm.run(cron_agent, messages=[{"role": "user", "content": "Commence daemon routine."}])
                    logger.info(f"[Chronos Daemon {job_id}] Output: {result_text}")
                else:
                    # Re-instantiate notification bounds with the secure async thread context
                    from app.services.notifications.notification_service import (
                        NotificationService,
                    )
                    from app.services.notifications.providers.database_provider import (
                        DatabaseNotificationProvider,
                    )
                    from app.services.notifications.providers.email_provider import (
                        EmailNotificationProvider,
                    )
                    from app.services.notifications.providers.push_provider import (
                        PushNotificationProvider,
                    )
                    
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
