import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.memory import Memory
from app.db.models.note import Note
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.services.ai.providers.router import ProviderRouter

logger = logging.getLogger(__name__)

class ReflectionLoop:
    """
    Simulates a Daily/Weekly Cron job that synthesizes short-term contextual memory fragments 
    into a coherent Journal entry.
    """
    def __init__(self, provider: ProviderRouter):
        self.provider = provider
    
    async def synthesize_daily_journal(self, user_id: int, session: AsyncSession) -> None:
        logger.info(f"Starting Reflection synthesis for user {user_id}")
        
        # Get memories generated in the past 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        
        result = await session.execute(
            select(Memory).where(Memory.user_id == user_id, Memory.created_at >= yesterday)
        )
        recent_memories = result.scalars().all()
        
        if not recent_memories:
            logger.info("No memories to synthesize.")
            return

        memory_context = "\n".join([f"- {m.key}: {m.value}" for m in recent_memories])
        
        prompt = f"""
        You are a highly perceptive system architect.
        Review the user's memories extracted over the past 24 hours and synthesize a single, concise Daily Reflection Note.
        Identify any implicit habits, state of mind, or actionable next-steps the user might not have explicitly asked for.
        
        Recent Memories:
        {memory_context}
        
        Return ONLY a beautifully drafted Markdown summary to be saved in their Notes app. No conversational intro.
        """
        
        try:
            messages = [{"role": "user", "content": prompt}]
            reflection_markdown = await self.provider.chat(messages, intent="general")
            
            note = Note(
                title=f"Reflection - {datetime.now(timezone.utc).strftime('%b %d, %Y')}",
                content=reflection_markdown,
                user_id=user_id,
                folder="Reflections",
                is_pinned=False
            )
            session.add(note)
            await session.commit()
            logger.info("Successfully concluded daily reflection cycle.")
            
        except Exception as e:
            logger.error(f"Failed to run reflection generation: {e}")

    async def synthesize_weekly_diff(self, user_id: int, session: AsyncSession) -> None:
        logger.info(f"Starting Weekly Memory Diff for user {user_id}")
        
        last_week = datetime.now(timezone.utc) - timedelta(days=7)
        old_week = datetime.now(timezone.utc) - timedelta(days=14)
        
        result_new = await session.execute(select(Memory).where(Memory.user_id == user_id, Memory.created_at >= last_week))
        result_old = await session.execute(select(Memory).where(Memory.user_id == user_id, Memory.created_at >= old_week, Memory.created_at < last_week))
        
        new_memories = result_new.scalars().all()
        old_memories = result_old.scalars().all()
        
        if not new_memories and not old_memories:
             return

        old_context = "\n".join([f"- {m.key}: {m.value}" for m in old_memories])
        new_context = "\n".join([f"- {m.key}: {m.value}" for m in new_memories])

        prompt = f"""
        Compare the user's memories, thoughts, and habits from this week versus last week.
        Highlight fundamental shifts in their mindset, behavior, or routines.
        Return ONLY a beautiful markdown summary. No fluff.
        
        Last Week Memories:
        {old_context}
        
        This Week Memories:
        {new_context}
        """
        
        try:
             diff_markdown = await self.provider.chat([{"role": "user", "content": prompt}], intent="general")
             note = Note(
                 title=f"Weekly Memory Diff - {datetime.now(timezone.utc).strftime('%b %d')}",
                 content=diff_markdown,
                 user_id=user_id,
                 folder="Reflections",
                 is_pinned=True
             )
             session.add(note)
             await session.commit()
             logger.info("Weekly memory diff saved successfully.")
        except Exception as e:
             logger.error(f"Failed to generate weekly diff: {e}")

    async def start_loop(self):
        """
        Runs unconditionally in the background in lifespan, checking if 5PM timezone.utc has hit.
        """
        while True:
            now = datetime.now(timezone.utc)
            # Example triggers everyday roughly dynamically 
            if now.hour == 17 and now.minute == 0:
                async with AsyncSessionLocal() as session:
                    users_res = await session.execute(select(User.id))
                    users = users_res.scalars().all()
                    for uid in users:
                        await self.synthesize_daily_journal(uid, session)
                        
            # Weekly Diff trigger on Sunday at 18:00
            if now.weekday() == 6 and now.hour == 18 and now.minute == 0:
                async with AsyncSessionLocal() as session:
                    users_res = await session.execute(select(User.id))
                    users = users_res.scalars().all()
                    for uid in users:
                        await self.synthesize_weekly_diff(uid, session)
            
            # Sleep until next minute
            await asyncio.sleep(60)

