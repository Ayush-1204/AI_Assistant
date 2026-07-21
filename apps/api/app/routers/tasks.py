import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.models.user import User
from app.dependencies import get_current_user, get_google_tasks_service
from app.integrations.google.tasks import GoogleTasksService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class TaskCreateReq(BaseModel):
    title: str
    priority: str = "Medium"
    due_date: str | None = None
    status: str = "To Do"
    notes: str | None = None

class TaskUpdateReq(BaseModel):
    title: str | None = None
    priority: str | None = None
    due_date: str | None = None
    status: str | None = None
    notes: str | None = None
    completed: bool | None = None

def _serialize_kanban_notes(notes: str | None, status: str, priority: str) -> str:
    metadata = {"status": status, "priority": priority}
    try:
        if notes and notes.startswith("<!--KANBAN:"):
            parts = notes.split("-->\n", 1)
            raw_notes = parts[1] if len(parts) > 1 else ""
        else:
            raw_notes = notes or ""
            
        metadata_str = f"<!--KANBAN:{json.dumps(metadata)}-->\n"
        return metadata_str + raw_notes
    except Exception:
        return notes or ""

def _deserialize_kanban_task(task_data: dict) -> dict:
    t = {
        "id": task_data.get("id"),
        "title": task_data.get("title", ""),
        "due": task_data.get("due"),
        "status": "Done" if task_data.get("status") == "completed" else "To Do",
        "priority": "Medium",
        "notes": "",
    }
    
    raw_notes = task_data.get("notes", "")
    if raw_notes.startswith("<!--KANBAN:"):
        parts = raw_notes.split("-->\n", 1)
        try:
            meta_json = parts[0].replace("<!--KANBAN:", "")
            meta = json.loads(meta_json)
            if t["status"] != "Done":
                t["status"] = meta.get("status", t["status"])
            t["priority"] = meta.get("priority", "Medium")
        except Exception:
            pass
        t["notes"] = parts[1] if len(parts) > 1 else ""
    else:
        t["notes"] = raw_notes
        
    return t

@router.post("")
async def create_task(req: TaskCreateReq, user: User = Depends(get_current_user), service: GoogleTasksService = Depends(get_google_tasks_service)):
    kanban_notes = _serialize_kanban_notes(req.notes, req.status, req.priority)
    res = await service.insert_task(
        user_id=user.id,
        title=req.title,
        notes=kanban_notes,
        due=req.due_date
    )
    return _deserialize_kanban_task(res)

@router.get("")
async def list_tasks(user: User = Depends(get_current_user), service: GoogleTasksService = Depends(get_google_tasks_service)):
    # Note: Google Tasks API pagination handles typically up to 100 tasks default.
    tasks = await service.get_tasks(user.id)
    return [_deserialize_kanban_task(t) for t in tasks]

@router.put("/{task_id}")
async def update_task(task_id: str, req: TaskUpdateReq, user: User = Depends(get_current_user), service: GoogleTasksService = Depends(get_google_tasks_service)):
    tasks = await service.get_tasks(user.id)
    current_task = next((t for t in tasks if t["id"] == task_id), None)
    if not current_task:
        raise HTTPException(status_code=404, detail="Task not found or is in an archived state.")
        
    parsed = _deserialize_kanban_task(current_task)
    
    new_status = req.status if req.status is not None else parsed["status"]
    new_priority = req.priority if req.priority is not None else parsed["priority"]
    new_notes_body = req.notes if req.notes is not None else parsed["notes"]
    
    google_status = None
    if req.completed is True or new_status == "Done":
        google_status = "completed"
    elif req.completed is False or new_status != "Done":
        google_status = "needsAction"
        
    if new_status == "Done" and google_status == "completed":
        # Google handles done status implicitly.
        pass
        
    kanban_notes = _serialize_kanban_notes(new_notes_body, new_status, new_priority)
    
    res = await service.update_task(
        user_id=user.id,
        task_id=task_id,
        title=req.title,
        notes=kanban_notes,
        due=req.due_date,
        status=google_status
    )
    return _deserialize_kanban_task(res)

@router.delete("/{task_id}")
async def delete_task(task_id: str, user: User = Depends(get_current_user), service: GoogleTasksService = Depends(get_google_tasks_service)):
    success = await service.delete_task(user.id, task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete task")
    return {"status": "ok"}
