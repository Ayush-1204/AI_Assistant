from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.models.user import User
from app.dependencies import get_current_user, get_reminder_service
from app.services.reminders.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["Reminders"])

class ReminderCreateReq(BaseModel):
    title: str
    reminder_time: datetime
    is_recurring: bool = False

@router.post("")
async def create_reminder(req: ReminderCreateReq, user: User = Depends(get_current_user), service: ReminderService = Depends(get_reminder_service)):
    return await service.create_reminder(user.id, req.title, req.reminder_time, req.is_recurring)

@router.get("")
async def list_reminders(user: User = Depends(get_current_user), service: ReminderService = Depends(get_reminder_service)):
    return await service.list_reminders(user.id)

@router.post("/{reminder_id}/complete")
async def complete_reminder(reminder_id: int, user: User = Depends(get_current_user), service: ReminderService = Depends(get_reminder_service)):
    return await service.mark_complete(reminder_id, user.id)

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: int, user: User = Depends(get_current_user), service: ReminderService = Depends(get_reminder_service)):
    return await service.delete_reminder(reminder_id, user.id)
