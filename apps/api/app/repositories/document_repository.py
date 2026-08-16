from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document
from app.db.models.document import DocumentStatus


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        document: Document,
    ) -> Document:

        self.db.add(document)

        await self.db.commit()

        await self.db.refresh(document)

        return document

    async def get_by_id(
        self,
        document_id: int,
    ) -> Document | None:

        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_sha256(
        self,
        sha256: str,
    ) -> Document | None:

        result = await self.db.execute(
            select(Document).where(
                Document.sha256 == sha256
            )
        )

        return result.scalars().first()

    async def count_by_storage_path(
        self,
        storage_path: str,
    ) -> int:

        result = await self.db.execute(
            select(func.count(Document.id)).where(
                Document.storage_path == storage_path
            )
        )

        return result.scalar_one()

    async def list_by_user(
        self,
        user_id: int,
        is_deleted: bool = False,
    ) -> list[Document]:

        result = await self.db.execute(
            select(Document)
            .where(
                Document.user_id == user_id,
                Document.is_deleted == is_deleted
            )
            .order_by(Document.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_expired_documents(
        self,
    ) -> list[Document]:

        result = await self.db.execute(
            select(Document)
            .where(Document.expires_at < func.now())
        )

        return list(result.scalars().all())

    async def update(
        self,
        document: Document,
    ) -> Document:

        await self.db.commit()

        await self.db.refresh(document)

        return document

    async def delete(
        self,
        document: Document,
    ) -> None:

        await self.db.delete(document)

        await self.db.commit()

    async def soft_delete(
        self,
        document: Document,
    ) -> None:

        document.is_deleted = True
        await self.db.commit()

    async def update_status(
        self,
        document: Document,
        status: DocumentStatus,
    ):
        document.status = status
        await self.update(document)