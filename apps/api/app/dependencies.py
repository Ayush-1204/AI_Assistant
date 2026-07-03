from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.config import settings

# Repositories
from app.repositories.user_repository import UserRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)

# Services
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.retrieval.fusion import ResultFusion
from app.services.retrieval.reranking import Reranker, CrossEncoderReranker


# AI
from app.services.ai.ai_service import AIService
from app.services.ai.providers import GeminiProvider
from app.services.ai.context import ContextBuilder
from app.services.ai.providers import OllamaProvider

# Embeddings
from app.services.ai.embeddings import (
    EmbeddingService,
)

from app.services.ai.embeddings.providers.gemini import (
    GeminiEmbeddingProvider,
)

from app.services.ai.embeddings.providers.ollama import (
    OllamaEmbeddingProvider,
)

from app.services.ai.embeddings.providers.base import (
    BaseEmbeddingProvider,
)

#  Indexing
from app.services.indexing import IndexingService

# Memory
from app.services.ai.memory import (
    MemoryExtractor,
    MemoryService,
)

# Tools
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.orchestrator import ToolOrchestrator
from app.services.ai.tools.datetime_tool import CurrentTimeTool
from app.services.ai.tools.calculator import CalculatorTool
from app.services.ai.tools.document_search import DocumentSearchTool
from app.services.ai.tools.memory_search import MemorySearchTool
from app.services.ai.tools.web_search import WebSearchTool
from app.integrations.search.tavily import TavilySearchProvider
from app.services.ai.tools.google_calendar import CalendarTool
from app.services.ai.tools.google_gmail import GmailTool
from app.services.ai.tools.google_drive import DriveTool
from app.integrations.google.auth import GoogleAuthService
from app.integrations.google.calendar import GoogleCalendarService
from app.integrations.google.gmail import GoogleGmailService
from app.integrations.google.drive import GoogleDriveService
from app.repositories.oauth_repository import OAuthRepository

# Documents
from app.services.documents.processor import DocumentProcessor
from app.services.documents.extractors.registry import (
    ExtractorRegistry,
)
from app.services.documents.chunking.text_chunker import (
    TextChunker,
)

# Utils
from app.utils.jwt import decode_access_token



oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


# ==========================================================
# Database
# ==========================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ==========================================================
# Repositories
# ==========================================================

def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_conversation_repository(
    db: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(db)


def get_message_repository(
    db: AsyncSession = Depends(get_db),
) -> MessageRepository:
    return MessageRepository(db)


def get_memory_repository(
    db: AsyncSession = Depends(get_db),
) -> MemoryRepository:
    return MemoryRepository(db)


def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    return DocumentRepository(db)


def get_document_chunk_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentChunkRepository:
    return DocumentChunkRepository(db)


# ==========================================================
# Core Services
# ==========================================================

def get_auth_service(
    repository: UserRepository = Depends(
        get_user_repository,
    ),
) -> AuthService:
    return AuthService(repository)


def get_conversation_service(
    repository: ConversationRepository = Depends(
        get_conversation_repository,
    ),
) -> ConversationService:
    return ConversationService(repository)


def get_message_service(
    message_repository: MessageRepository = Depends(
        get_message_repository,
    ),
    conversation_repository: ConversationRepository = Depends(
        get_conversation_repository,
    ),
) -> MessageService:
    return MessageService(
        message_repository=message_repository,
        conversation_repository=conversation_repository,
    )


# ==========================================================
# AI Provider
# ==========================================================
from app.services.ai.providers.router import ProviderRouter

_router_instance = None

def get_provider_router() -> ProviderRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = ProviderRouter()
        _router_instance.register_provider(GeminiProvider())
        _router_instance.register_provider(OllamaProvider())
    return _router_instance


# ==========================================================
# Memory
# ==========================================================

def get_memory_extractor(
    provider: ProviderRouter = Depends(
        get_provider_router,
    ),
) -> MemoryExtractor:

    return MemoryExtractor(provider)


def get_memory_service(
    repository: MemoryRepository = Depends(
        get_memory_repository,
    ),
    extractor: MemoryExtractor = Depends(
        get_memory_extractor,
    ),
) -> MemoryService:

    return MemoryService(
        repository,
        extractor,
    )


# ==========================================================
# Document Components
# ==========================================================

def get_storage_service() -> StorageService:
    return StorageService()


def get_extractor_registry() -> ExtractorRegistry:
    return ExtractorRegistry()


def get_text_chunker() -> TextChunker:
    return TextChunker(
        chunk_size=settings.rag_chunk_size,
        overlap=settings.rag_chunk_overlap,
    )


def get_embedding_provider() -> BaseEmbeddingProvider:
    return OllamaEmbeddingProvider()


def get_embedding_service(
    provider: BaseEmbeddingProvider = Depends(
        get_embedding_provider,
    ),
) -> EmbeddingService:

    return EmbeddingService(
        provider,
    )

#
#
#

_fusion_instance = None
_reranker_instance = None

def get_result_fusion() -> ResultFusion:
    global _fusion_instance
    if _fusion_instance is None:
        _fusion_instance = ResultFusion()
    return _fusion_instance

def get_reranker() -> Reranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker()
    return _reranker_instance


def get_retrieval_service(

    chunk_repository: DocumentChunkRepository = Depends(
        get_document_chunk_repository,
    ),

    embedding_service: EmbeddingService = Depends(
        get_embedding_service,
    ),
    
    result_fusion: ResultFusion = Depends(
        get_result_fusion,
    ),
    
    reranker: Reranker = Depends(
        get_reranker,
    ),

) -> RetrievalService:

    return RetrievalService(
        chunk_repository=chunk_repository,
        embedding_service=embedding_service,
        result_fusion=result_fusion,
        reranker=reranker,
    )


# ==========================================================
# Context Builder
# ==========================================================

def get_context_builder(
    message_service: MessageService = Depends(
        get_message_service,
    ),
    memory_service: MemoryService = Depends(
        get_memory_service,
    ),
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service,
    ),
) -> ContextBuilder:

    return ContextBuilder(
        message_service=message_service,
        memory_service=memory_service,
        retrieval_service=retrieval_service,
    )


def get_indexing_service(
    chunk_repository: DocumentChunkRepository = Depends(
        get_document_chunk_repository,
    ),
    document_repository: DocumentRepository = Depends(
        get_document_repository,
    ),
    embedding_service: EmbeddingService = Depends(
        get_embedding_service,
    ),
) -> IndexingService:

    return IndexingService(
        chunk_repository=chunk_repository,
        document_repository=document_repository,
        embedding_service=embedding_service,
    )


def get_document_processor(
    document_repository: DocumentRepository = Depends(
        get_document_repository,
    ),
    chunk_repository: DocumentChunkRepository = Depends(
        get_document_chunk_repository,
    ),
    extractor_registry: ExtractorRegistry = Depends(
        get_extractor_registry,
    ),
    chunker: TextChunker = Depends(
        get_text_chunker,
    ),
    indexing_service: IndexingService = Depends(
        get_indexing_service,
    ),
) -> DocumentProcessor:

    return DocumentProcessor(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        extractor_registry=extractor_registry,
        chunker=chunker,
        indexing_service=indexing_service,
    )


def get_document_service(
    repository: DocumentRepository = Depends(
        get_document_repository,
    ),
    storage_service: StorageService = Depends(
        get_storage_service,
    ),
    processor: DocumentProcessor = Depends(
        get_document_processor,
    ),
) -> DocumentService:

    return DocumentService(
        repository=repository,
        storage_service=storage_service,
        processor=processor,
    )

# ==========================================================
# Tool Orchestrator
# ==========================================================

def get_tool_orchestrator(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    memory_service: MemoryService = Depends(get_memory_service),
    db: AsyncSession = Depends(get_db),
) -> ToolOrchestrator:

    registry = ToolRegistry()
    registry.register(CurrentTimeTool())
    registry.register(CalculatorTool())
    registry.register(DocumentSearchTool(retrieval_service))
    registry.register(MemorySearchTool(memory_service))
    
    if settings.GOOGLE_CLIENT_ID:
        oauth_repo = OAuthRepository(db)
        auth_service = GoogleAuthService(oauth_repo)
        
        registry.register(CalendarTool(GoogleCalendarService(auth_service)))
        registry.register(GmailTool(GoogleGmailService(auth_service)))
        registry.register(DriveTool(GoogleDriveService(auth_service)))
    
    if settings.enable_web_search:
        search_provider = None
        if settings.default_search_provider == "tavily":
            search_provider = TavilySearchProvider()
        
        if search_provider:
            registry.register(WebSearchTool(search_provider))
            
    return ToolOrchestrator(registry)

# ==========================================================
# AI Service
# ==========================================================

def get_ai_service(
    provider: ProviderRouter = Depends(
        get_provider_router,
    ),
    message_service: MessageService = Depends(
        get_message_service,
    ),
    conversation_service: ConversationService = Depends(
        get_conversation_service,
    ),
    context_builder: ContextBuilder = Depends(
        get_context_builder,
    ),
    memory_service: MemoryService = Depends(
        get_memory_service,
    ),
    tool_orchestrator: ToolOrchestrator = Depends(
        get_tool_orchestrator,
    ),
) -> AIService:

    return AIService(
        provider=provider,
        message_service=message_service,
        conversation_service=conversation_service,
        context_builder=context_builder,
        memory_service=memory_service,
        tool_orchestrator=tool_orchestrator,
    )


# ==========================================================
# Authentication
# ==========================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repository: UserRepository = Depends(
        get_user_repository,
    ),
):
    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await repository.get_by_id(
        int(user_id),
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user