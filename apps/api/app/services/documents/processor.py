from pathlib import Path

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
)
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.services.documents.chunking.text_chunker import (
    TextChunker,
)
from app.services.documents.extractors.registry import (
    ExtractorRegistry,
)
from app.services.documents.mappers.chunk_mapper import ChunkMapper


class DocumentProcessor:

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
        extractor_registry: ExtractorRegistry,
        chunker: TextChunker,
    ):
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.registry = extractor_registry
        self.chunker = chunker

    async def process(
        self,
        document: Document,
    ) -> None:

        try:

            await self.document_repository.update_status(
                document,
                DocumentStatus.EXTRACTING,
            )

            extractor = self.registry.get(
                Path(document.storage_path),
            )

            extracted = await extractor.extract(
                Path(document.storage_path)
            )

            document.page_count = extracted.page_count

            document.language = extracted.metadata.get(
                "language",
            )

            if extracted.title:
                document.title = extracted.title

            await self.document_repository.update_status(
                document,
                DocumentStatus.CHUNKING,
            )

            chunks = self.chunker.chunk(
                extracted,
            )

            models = ChunkMapper.to_models(
                document_id=document.id,
                chunks=chunks,
            )

            await self.chunk_repository.create_many(
                models,
            )

            await self.document_repository.update_status(
                document,
                DocumentStatus.READY,
            )

        except Exception:

            await self.document_repository.update_status(
                document,
                DocumentStatus.FAILED,
            )

            raise