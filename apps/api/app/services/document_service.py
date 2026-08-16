import logging
from datetime import datetime, timezone, timedelta
from fastapi import BackgroundTasks, HTTPException, UploadFile, status

from app.db.models import Document, DocumentStatus, DocumentChunk
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.documents.processor import DocumentProcessor
from app.services.documents.background import process_document_background_task
from app.services.storage_service import StorageService


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        storage_service: StorageService,
        processor: DocumentProcessor,
        chunk_repository: DocumentChunkRepository,
    ):
        self.repository = repository
        self.storage_service = storage_service
        self.processor = processor
        self.chunk_repository = chunk_repository
    async def upload(
        self,
        *,
        user_id: int,
        title: str,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> Document:

        if file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename",
            )

        (
            stored_filename,
            storage_path,
            sha256,
        ) = self.storage_service.save(
            user_id=user_id,
            file=file,
        )

        existing = await self.repository.get_by_sha256(
            sha256,
        )

        if existing is not None and existing.status == DocumentStatus.READY:
            self.storage_service.delete(storage_path)

            document = Document(
                user_id=user_id,
                title=title,
                original_filename=file.filename,
                stored_filename=stored_filename,
                mime_type=existing.mime_type,
                file_size=existing.file_size,
                sha256=sha256,
                storage_path=existing.storage_path,
                status=DocumentStatus.READY,
                page_count=existing.page_count,
                language=existing.language,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )

            document = await self.repository.create(document)

            chunks = await self.chunk_repository.list_by_document(existing.id)
            new_chunks = [
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    chunk_metadata=chunk.chunk_metadata,
                    embedding=chunk.embedding
                ) for chunk in chunks
            ]
            
            if new_chunks:
                await self.chunk_repository.create_many(new_chunks)

            return document

        document = Document(
            user_id=user_id,
            title=title,
            original_filename=file.filename,
            stored_filename=stored_filename,
            mime_type=file.content_type,
            file_size=file.size or 0,
            sha256=sha256,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        document = await self.repository.create(
            document,
        )
    
        background_tasks.add_task(
            process_document_background_task,
            document_id=document.id,
        )   

        return document

    async def get(
        self,
        *,
        document_id: int,
        user_id: int,
    ) -> Document:

        document = await self.repository.get_by_id(
            document_id,
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if document.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return document

    async def list(
        self,
        *,
        user_id: int,
        is_deleted: bool = False,
    ) -> list[Document]:

        return await self.repository.list_by_user(
            user_id,
            is_deleted=is_deleted,
        )

    async def delete(
        self,
        *,
        document_id: int,
        user_id: int,
        hard: bool = False,
    ) -> None:

        document = await self.get(
            document_id=document_id,
            user_id=user_id,
        )

        if not hard:
            await self.repository.soft_delete(document)
            return

        count = await self.repository.count_by_storage_path(
            document.storage_path,
        )

        if count <= 1:
            self.storage_service.delete(
                document.storage_path,
            )

        await self.repository.delete(
            document,
        )

    async def delete_expired(self) -> None:
        logger = logging.getLogger(__name__)
        expired_docs = await self.repository.get_expired_documents()
        
        for doc in expired_docs:
            try:
                # Same safe-deletion logic as normal delete
                count = await self.repository.count_by_storage_path(doc.storage_path)
                if count <= 1:
                    self.storage_service.delete(doc.storage_path)
                
                await self.repository.delete(doc)
                logger.info(f"Deleted expired document {doc.id}")
            except Exception as e:
                logger.error(f"Failed to delete expired document {doc.id}: {e}")