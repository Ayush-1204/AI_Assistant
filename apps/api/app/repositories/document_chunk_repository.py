from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
)
from app.services.retrieval.models import RetrievalResult


class DocumentChunkRepository:
    """
    Repository responsible for DocumentChunk persistence and retrieval.

    This repository contains only data-access logic.
    Semantic search returns raw database results (chunk + cosine distance).
    Business logic such as thresholding, reranking, or filtering belongs
    in the RetrievalService.
    """

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
    ) -> None:

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
    ) -> None:

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

    async def semantic_search(
        self,
        embedding: list[float],
        user_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Perform semantic search using pgvector cosine distance.

        Returns:
            list of RetrievalResult objects containing the chunk and
            cosine distance.

        Results are ordered by ascending cosine distance.

        No thresholding or business logic is applied here.
        """

        distance = (
            DocumentChunk.embedding
            .cosine_distance(embedding)
            .label("distance")
        )

        stmt = (
            select(
                DocumentChunk,
                distance,
            )
            .join(Document)
            .where(
                Document.user_id == user_id,
                Document.status == DocumentStatus.READY,
            )
            .order_by(distance.asc())
            .limit(top_k)
            .options(
                selectinload(DocumentChunk.document)
            )
        )

        result = await self.db.execute(stmt)

        return [
            RetrievalResult(
                chunk=row[0],
                distance=float(row[1]),
            )
            for row in result.all()
        ]