from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
)


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
        query: str,
        embedding: list[float],
        user_id: int,
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Perform semantic search using pgvector cosine distance.

        Returns:
            list of (DocumentChunk, cosine_distance) tuples.

        Results are ordered by ascending cosine distance.

        No thresholding or business logic is applied here.
        """

        distance = (
            DocumentChunk.embedding
            .cosine_distance(embedding)
        )

        match_score = case(
            (DocumentChunk.content.ilike(f"%{query}%"), 0.0),
            else_=distance
        ).label("match_score")

        stmt = (
            select(
                DocumentChunk,
                match_score,
            )
            .join(Document)
            .where(
                Document.user_id == user_id,
                Document.status == DocumentStatus.READY,
            )
            .order_by(match_score.asc(), distance.asc())
            .limit(top_k)
            .options(
                selectinload(DocumentChunk.document)
            )
        )

        result = await self.db.execute(stmt)

        return [
            (
                row[0],
                float(row[1]),
            )
            for row in result.all()
        ]