import asyncio
from pathlib import Path

from app.db.models.document import Document, DocumentStatus
from app.db.models.note import Note
from app.repositories.document_repository import DocumentRepository
from app.repositories.note_repository import NoteRepository
from app.services.documents.processor import DocumentProcessor
from app.services.documents.background import process_document_background_task


class NoteService:
    def __init__(
        self,
        note_repository: NoteRepository,
        document_repository: DocumentRepository,
        document_processor: DocumentProcessor,
    ):
        self.note_repository = note_repository
        self.document_repository = document_repository
        self.document_processor = document_processor
        self.storage_dir = Path("data/notes")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def create_note(
        self, user_id: int, title: str, content: str, folder: str | None = None, tags: list[str] | None = None
    ) -> Note:
        note = Note(
            user_id=user_id,
            title=title,
            content=content,
            folder=folder,
            tags=tags or []
        )
        note = await self.note_repository.create(note)
        
        import hashlib
        file_path = self.storage_dir / f"note_{note.id}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        file_size = len(content.encode('utf-8'))
        sha256_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
        doc = Document(
            title=title,
            original_filename=f"note_{note.id}.txt",
            stored_filename=f"note_stored_{note.id}.txt",
            mime_type="text/plain",
            file_size=file_size,
            sha256=sha256_hash,
            storage_path=str(file_path),
            user_id=user_id,
            status=DocumentStatus.UPLOADED
        )
        doc = await self.document_repository.create(doc)
        
        note.document_id = doc.id
        await self.note_repository.update(note)
        
        asyncio.create_task(process_document_background_task(doc.id))
        
        return note

    async def get_note(self, note_id: int, user_id: int) -> Note | None:
        return await self.note_repository.get_by_id(note_id, user_id)

    async def list_notes(self, user_id: int) -> list[Note]:
        return await self.note_repository.list_by_user(user_id)

    async def update_note(self, note_id: int, user_id: int, updates: dict) -> Note | None:
        note = await self.note_repository.get_by_id(note_id, user_id)
        if not note:
            return None
            
        for k, v in updates.items():
            if hasattr(note, k):
                setattr(note, k, v)
        
        note = await self.note_repository.update(note)
        
        if "content" in updates or "title" in updates:
            import hashlib
            file_path = self.storage_dir / f"note_{note.id}.txt"
            content_str = str(note.content)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_str)
            
            if note.document_id is not None:
                doc = await self.document_repository.get_by_id(int(note.document_id))
                if doc:
                    doc.title = str(note.title)
                    doc.file_size = len(content_str.encode('utf-8'))
                    doc.sha256 = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
                    doc.status = DocumentStatus.UPLOADED
                    await self.document_repository.update(doc)
                    
                    # Instead of creating duplicate chunks randomly, we should optimally 
                    # let DocumentProcessor handle chunks gracefully, 
                    # but for now running this again will embed it linearly!
                    asyncio.create_task(process_document_background_task(doc.id))
                    
        return note

    async def delete_note(self, note_id: int, user_id: int) -> bool:
        note = await self.note_repository.get_by_id(note_id, user_id)
        if not note:
            return False
            
        if note.document_id is not None:
            doc = await self.document_repository.get_by_id(int(note.document_id))
            if doc:
                await self.document_repository.delete(doc)
                
        file_path = self.storage_dir / f"note_{note.id}.txt"
        if file_path.exists():
            file_path.unlink()
            
        await self.note_repository.delete(note)
        return True
