from fastapi import HTTPException, UploadFile, status, BackgroundTasks

from app.db.models import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import StorageService
from app.services.documents.processor import DocumentProcessor




class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        storage_service: StorageService,
        processor: DocumentProcessor,
    ):
        self.repository = repository
        self.storage_service = storage_service
        self.processor = processor
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

        if existing is not None:

            self.storage_service.delete(
                storage_path,
            )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document already exists.",
            )

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
        )

        document = await self.repository.create(
            document,
        )
    
        background_tasks.add_task(
            self.processor.process,
            document=document,
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
    ) -> list[Document]:

        return await self.repository.list_by_user(
            user_id,
        )

    async def delete(
        self,
        *,
        document_id: int,
        user_id: int,
    ) -> None:

        document = await self.get(
            document_id=document_id,
            user_id=user_id,
        )

        self.storage_service.delete(
            document.storage_path,
        )

        await self.repository.delete(
            document,
        )