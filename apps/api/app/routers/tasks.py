from typing import Any
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_task_service
from app.db.models.user import User
from app.services.tasks.task_service import TaskService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class TaskCreateReq(BaseModel):
    title: str
    priority: int = 1
    due_date: datetime | None = None
    project: str | None = None
    tags: list[str] | None = None

@router.post("")
async def create_task(req: TaskCreateReq, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return await service.create_task(user.id, req.title, req.priority, req.due_date, req.project, req.tags)

@router.get("")
async def list_tasks(user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return await service.list_tasks(user.id)

@router.post("/{task_id}/complete")
async def complete_task(task_id: int, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return await service.mark_complete(task_id, user.id)

@router.delete("/{task_id}")
async def delete_task(task_id: int, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return await service.delete_task(task_id, user.id)
