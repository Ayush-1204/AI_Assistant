import asyncio
from typing import Optional

from app.db.session import AsyncSessionLocal
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.documents.processor import DocumentProcessor
from app.services.documents.extractors.registry import ExtractorRegistry
from app.services.documents.chunking.text_chunker import TextChunker
from app.services.indexing.indexing_service import IndexingService
from app.services.ai.embeddings.providers.ollama import OllamaEmbeddingProvider
from app.services.ai.embeddings.providers.gemini import GeminiEmbeddingProvider
from app.services.ai.embeddings import EmbeddingService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def process_document_background_task(document_id: int):
    """
    Executes the document processing pipeline inside its own database session.
    This prevents InterfaceError crashes that occur when background tasks share
    the HTTP request's session which gets closed when the request returns.
    """
    async with AsyncSessionLocal() as session:
        try:
            doc_repo = DocumentRepository(session)
            chunk_repo = DocumentChunkRepository(session)
            
            doc = await doc_repo.get_by_id(document_id)
            if not doc:
                logger.warning(f"Document {document_id} not found for background processing.")
                return

            extractor_reg = ExtractorRegistry()
            chunker = TextChunker()
            
            # Setup embedding service 
            # (Note: In a real DI container this would be injected, but for 
            # background tasks we instantiate the pipeline)
            provider = OllamaEmbeddingProvider()
                
            embedding_service = EmbeddingService(provider)
            idx_svc = IndexingService(chunk_repo, doc_repo, embedding_service)
            
            processor = DocumentProcessor(doc_repo, chunk_repo, extractor_reg, chunker, idx_svc)
            
            await processor.process(doc)
            
        except Exception as e:
            logger.exception(f"Error in background document processing for doc {document_id}: {e}")

async def document_cleanup_loop():
    """
    Background daemon that runs periodically to find and delete expired documents.
    """
    from app.services.document_service import DocumentService
    from app.services.storage_service import StorageService
    
    logger.info("Starting document cleanup loop...")
    while True:
        try:
            # Wake up every hour to clean up
            await asyncio.sleep(3600)
            
            async with AsyncSessionLocal() as session:
                doc_repo = DocumentRepository(session)
                chunk_repo = DocumentChunkRepository(session)
                storage_svc = StorageService()
                
                # Mock a processor since delete_expired doesn't use it
                doc_svc = DocumentService(doc_repo, storage_svc, None, chunk_repo) # type: ignore
                
                await doc_svc.delete_expired()
                
        except asyncio.CancelledError:
            logger.info("Document cleanup loop stopped.")
            break
        except Exception as e:
            logger.exception(f"Error in document cleanup loop: {e}")
            await asyncio.sleep(60) # Wait a bit before retrying on error
