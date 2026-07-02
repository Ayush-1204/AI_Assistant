import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Documents", "AI_Assistant", "apps", "api")))

from app.db.session import AsyncSessionLocal
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.ai.embeddings.providers.ollama import OllamaEmbeddingProvider
from app.services.ai.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.retrieval_service import RetrievalService

logging.basicConfig(level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def main():
    async with AsyncSessionLocal() as session:
        chunk_repo = DocumentChunkRepository(session)
        emb_provider = OllamaEmbeddingProvider()
        emb_service = EmbeddingService(emb_provider)
        ret_service = RetrievalService(emb_service, chunk_repo)

        print("\n\n======== RUNNING PURE FALLBACK TEST ========")
        for query in ["dlcv", "what is dlcv"]:
            print(f"Query: {query}")
            results = await ret_service.retrieve(query=query, user_id=1, top_k=5)
            print(f"Results Array Length Returned: {len(results)}\n")

if __name__ == "__main__":
    asyncio.run(main())
