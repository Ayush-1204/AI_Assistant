from app.db.models import DocumentChunk
from app.services.documents.models import Chunk


class ChunkMapper:

    @staticmethod
    def to_model(
        *,
        document_id: int,
        chunk: Chunk,
    ) -> DocumentChunk:

        return DocumentChunk(
            document_id=document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            token_count=chunk.token_count,
            chunk_metadata=chunk.metadata,
        )

    @staticmethod
    def to_models(
        *,
        document_id: int,
        chunks: list[Chunk],
    ) -> list[DocumentChunk]:

        return [
            ChunkMapper.to_model(
                document_id=document_id,
                chunk=chunk,
            )
            for chunk in chunks
        ]