from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)

from app.repositories.document_repository import (
    DocumentRepository,
)

from app.db.models import DocumentStatus

from app.services.ai.embeddings import (
    EmbeddingService,
)


class IndexingService:

    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        document_repository: DocumentRepository,
        embedding_service: EmbeddingService,
    ):
        self.chunk_repository = chunk_repository
        self.document_repository = document_repository
        self.embedding_service = embedding_service

    async def index_document(
        self,
        document_id: int,
    ):

        document = await self.document_repository.get_by_id(
            document_id,
        )

        await self.document_repository.update_status(
            document,
            DocumentStatus.EMBEDDING,
        )

        chunks = await self.chunk_repository.list_by_document(
            document_id,
        )

        for chunk in chunks:

            embedding = await self.embedding_service.embed(
                chunk.content,
            )

            #
            chunk.embedding = embedding
            #
        
        await self.chunk_repository.update_many(
            chunks,
        )

        await self.document_repository.update_status(
            document,
            DocumentStatus.READY,
        )