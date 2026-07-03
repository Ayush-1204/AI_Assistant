from typing import Any
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_note_service
from app.db.models.user import User
from app.services.notes.note_service import NoteService
from pydantic import BaseModel

router = APIRouter(prefix="/notes", tags=["Notes"])

class NoteCreateReq(BaseModel):
    title: str
    content: str
    folder: str | None = None
    tags: list[str] | None = None

class NoteUpdateReq(BaseModel):
    title: str | None = None
    content: str | None = None

@router.post("")
async def create_note(req: NoteCreateReq, user: User = Depends(get_current_user), service: NoteService = Depends(get_note_service)):
    return await service.create_note(user.id, req.title, req.content, req.folder, req.tags)

@router.get("")
async def list_notes(user: User = Depends(get_current_user), service: NoteService = Depends(get_note_service)):
    return await service.list_notes(user.id)

@router.get("/{note_id}")
async def get_note(note_id: int, user: User = Depends(get_current_user), service: NoteService = Depends(get_note_service)):
    return await service.get_note(note_id, user.id)

@router.patch("/{note_id}")
async def update_note(note_id: int, req: NoteUpdateReq, user: User = Depends(get_current_user), service: NoteService = Depends(get_note_service)):
    return await service.update_note(note_id, user.id, req.model_dump(exclude_unset=True))

@router.delete("/{note_id}")
async def delete_note(note_id: int, user: User = Depends(get_current_user), service: NoteService = Depends(get_note_service)):
    return await service.delete_note(note_id, user.id)
