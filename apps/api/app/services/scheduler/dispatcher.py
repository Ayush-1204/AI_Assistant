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
                    logger.info(f"[Dispatcher] Spawning autonomous chat execution for {job_id}...")
                    
                    # 1. Find or create the conversation thread for this specific job
                    from app.db.models.conversation import Conversation
                    from sqlalchemy import select
                    
                    convo_title = f"Daemon: {job.label}"
                    convo_result = await session.execute(
                        select(Conversation)
                        .where(Conversation.user_id == job.user_id, Conversation.title == convo_title)
                        .limit(1)
                    )
                    convo = convo_result.scalar_one_or_none()
                    
                    if not convo:
                        convo = Conversation(title=convo_title, user_id=job.user_id, is_pinned=True)
                        session.add(convo)
                        await session.flush()
                        await session.commit()
                        
                    # 2. Re-instantiate the main AIService context for the job
                    from app.dependencies import get_ai_service_standalone
                    ai_service = get_ai_service_standalone(session)
                    
                    # 3. Formulate the autonomous prompt
                    from datetime import datetime
                    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                    
                    prompt = (
                        f"[AUTOMATED SCHEDULED TRIGGER]\n"
                        f"Date: {now_str}\n"
                        f"Title: {job.label}\n"
                        f"{job.recurring_action}"
                    )
                    
                    from app.db.models.user import User
                    user_result = await session.execute(select(User).where(User.id == job.user_id))
                    user = user_result.scalar_one_or_none()
                    
                    # 4. Execute standard chat pipeline natively
                    # This will automatically inject the user's prompt into the conversation,
                    # run tool strategy loops (searching the web, time, etc),
                    # and append the final response back into the same conversation.
                    result_text, citations, metadata = await ai_service.chat(
                        user_id=job.user_id,
                        conversation_id=convo.id,
                        prompt=prompt,
                        location_lat=user.last_known_lat if user else None,
                        location_lon=user.last_known_lon if user else None,
                        intent="general"
                    )
                    
                    logger.info(f"[Dispatcher {job_id}] Execution completed via AIService. Latency: {metadata.get('latency_ms')}ms")
                    
                    # 5. Ensure the user receives a push notification linking to the chat
                    from app.services.notifications.notification_service import NotificationService
                    from app.services.notifications.providers.database_provider import DatabaseNotificationProvider
                    from app.services.notifications.providers.push_provider import PushNotificationProvider
                    
                    notif_svc = NotificationService([
                        DatabaseNotificationProvider(session),
                        PushNotificationProvider(session)
                    ])
                    
                    snippet = result_text[:200] + ("..." if len(result_text) > 200 else "")
                    await notif_svc.notify(
                         job.user_id,
                         title=f"Autonomous Update: {job.label}", 
                         message=f"{snippet}",
                         type="SYSTEM", priority=1,
                         data={"conversation_id": convo.id}
                    )
                else:
                    # Re-instantiate notification bounds with the secure async thread context
                    from app.services.notifications.notification_service import (
                        NotificationService,
                    )
                    from app.services.notifications.providers.database_provider import (
                        DatabaseNotificationProvider,
                    )
                    from app.services.notifications.providers.push_provider import (
                        PushNotificationProvider,
                    )
                    
                    notif_svc = NotificationService([
                        DatabaseNotificationProvider(session),
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
