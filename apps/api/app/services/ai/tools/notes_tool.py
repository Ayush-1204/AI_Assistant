from typing import Any
from app.services.ai.tools.base import BaseTool
from app.services.notes.note_service import NoteService

class NotesTool(BaseTool):
    def __init__(self, note_service: NoteService):
        self.note_service = note_service

    @property
    def name(self) -> str:
        return "notes"

    @property
    def description(self) -> str:
        return "Create, update, search, and list personal notes. NOTE: Search content inside notes via `document_search` instead since Notes are automatically indexed. This tool is strictly for CRUD and viewing metadata."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "list", "get", "update", "delete"]},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "note_id": {"type": "integer"},
                "folder": {"type": "string"},
            },
            "required": ["action"]
        }

    async def execute(self, execution_context: dict[str, Any], **kwargs: Any) -> Any:
        user_id = execution_context.get("user_id")
        if user_id is None:
            return "Error: missing user_id"
        action = kwargs.get("action")
        
        if action == "create":
            note = await self.note_service.create_note(user_id, kwargs["title"], kwargs.get("content", ""), kwargs.get("folder"))
            return f"Note '{note.title}' created with ID {note.id}."
        elif action == "list":
            notes = await self.note_service.list_notes(user_id)
            return [{"id": n.id, "title": n.title, "folder": n.folder} for n in notes]
        elif action == "get":
            note = await self.note_service.get_note(kwargs["note_id"], user_id)
            return note.content if note else "Note not found."
        elif action == "update":
            updates = {}
            if "title" in kwargs: updates["title"] = kwargs["title"]
            if "content" in kwargs: updates["content"] = kwargs["content"]
            note = await self.note_service.update_note(kwargs["note_id"], user_id, updates)
            return "Note updated successfully." if note else "Note not found."
        elif action == "delete":
            success = await self.note_service.delete_note(kwargs["note_id"], user_id)
            return "Note deleted." if success else "Note not found."
