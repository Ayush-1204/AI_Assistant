from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunk


class DocumentChunkRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        chunk: DocumentChunk,
    ) -> DocumentChunk:

        self.db.add(chunk)

        await self.db.commit()

        await self.db.refresh(chunk)

        return chunk

    async def create_many(
        self,
        chunks: list[DocumentChunk],
    ):

        self.db.add_all(chunks)

        await self.db.commit()

    async def list_by_document(
        self,
        document_id: int,
    ) -> list[DocumentChunk]:

        result = await self.db.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id
            )
            .order_by(
                DocumentChunk.chunk_index.asc()
            )
        )

        return list(result.scalars().all())

    async def delete_by_document(
        self,
        document_id: int,
    ):

        chunks = await self.list_by_document(
            document_id,
        )

        for chunk in chunks:
            await self.db.delete(chunk)

        await self.db.commit()

    async def update(
        self,
        chunk: DocumentChunk,
    ) -> DocumentChunk:

        self.db.add(chunk)

        await self.db.commit()

        await self.db.refresh(chunk)

        return chunk
    
    async def update_many(
        self,
        chunks: list[DocumentChunk],
    ) -> None:

        self.db.add_all(chunks)

        await self.db.commit()