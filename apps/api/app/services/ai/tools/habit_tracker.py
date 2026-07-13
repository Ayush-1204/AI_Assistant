import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models.habit import Habit, HabitLog
from app.db.session import AsyncSessionLocal
from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class HabitTrackerTool(BaseTool):
    @property
    def name(self) -> str:
        return "habit_tracker"
        
    @property
    def description(self) -> str:
        return "Track user activities and recurring habits. Use this anytime the user mentions completing a daily goal, workout, diet milestone, or wants to check their habit streaks."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action: 'get_all', 'log_completion', 'create_habit'.",
                    "enum": ["get_all", "log_completion", "create_habit"]
                },
                "habit_name": {
                    "type": "string",
                    "description": "Name of the habit to log or create (e.g. 'gym', 'read 10 pages')."
                },
                "note": {
                    "type": "string",
                    "description": "Optional details about the completion (e.g. 'Hit a new PR')."
                }
            },
            "required": ["action"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> str:
        user_id = execution_context.get("user_id")
        action = kwargs.get("action")
        habit_name = kwargs.get("habit_name", "").strip().lower()
        note = kwargs.get("note", "")

        if not user_id:
            return "ERROR: user_id missing from context."

        async with AsyncSessionLocal() as session:
            if action == "get_all":
                result = await session.execute(select(Habit).where(Habit.user_id == user_id))
                habits = result.scalars().all()
                if not habits:
                    return "No habits tracking."
                
                return "\\n".join([f"- {h.name.title()}: {h.current_streak} streak. Target: {h.frequency_target}/week." for h in habits])
                
            elif action == "create_habit":
                if not habit_name:
                    return "ERROR: habit_name required."
                    
                existing = await session.execute(select(Habit).where(Habit.user_id == user_id, Habit.name == habit_name))
                if existing.scalars().first():
                    return f"Habit '{habit_name}' already exists!"
                    
                new_habit = Habit(user_id=user_id, name=habit_name)
                session.add(new_habit)
                await session.commit()
                return f"Created habit '{habit_name}' successfully."
                
            elif action == "log_completion":
                if not habit_name:
                    return "ERROR: habit_name required."
                    
                existing = await session.execute(select(Habit).where(Habit.user_id == user_id, Habit.name == habit_name))
                habit = existing.scalars().first()
                if not habit:
                    # Auto create
                    habit = Habit(user_id=user_id, name=habit_name, current_streak=0, longest_streak=0)
                    session.add(habit)
                    await session.flush()
                
                # Check if already logged today
                today = datetime.now(timezone.utc).date()
                last_logs = await session.execute(
                    select(HabitLog).where(HabitLog.habit_id == habit.id).order_by(HabitLog.completed_at.desc())
                )
                last_log = last_logs.scalars().first()
                
                if last_log and getattr(last_log.completed_at, "date", lambda: None)() == today:
                     return f"Already logged '{habit.name}' for today!"
                     
                new_log = HabitLog(habit_id=habit.id, note=note)
                habit.current_streak += 1
                if habit.current_streak > habit.longest_streak:
                    habit.longest_streak = habit.current_streak
                    
                session.add(new_log)
                await session.commit()
                
                return f"Logged '{habit.name}' completion! New streak: {habit.current_streak}."
                
            return "ERROR: Unknown action."
