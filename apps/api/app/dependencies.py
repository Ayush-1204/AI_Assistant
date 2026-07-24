from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.google.auth import GoogleAuthService
from app.integrations.google.calendar import GoogleCalendarService
from app.integrations.google.drive import GoogleDriveService
from app.integrations.google.gmail import GoogleGmailService
from app.integrations.google.tasks import GoogleTasksService
from app.integrations.search.tavily import TavilySearchProvider
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_repository import DocumentRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.oauth_repository import OAuthRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.task_repository import TaskRepository

# Repositories
from app.repositories.user_repository import UserRepository

# AI
from app.services.ai.ai_service import AIService
from app.services.ai.context import ContextBuilder

# Embeddings
from app.services.ai.embeddings import (
    EmbeddingService,
)
from app.services.ai.embeddings.providers.base import (
    BaseEmbeddingProvider,
)
from app.services.ai.embeddings.providers.ollama import (
    OllamaEmbeddingProvider,
)

# Memory
from app.services.ai.memory import (
    MemoryExtractor,
    MemoryService,
)
from app.services.ai.providers import GeminiProvider, OllamaProvider
from app.services.ai.tools.calculator import CalculatorTool
from app.services.ai.tools.datetime_tool import CurrentTimeTool
from app.services.ai.tools.document_search import DocumentSearchTool
from app.services.ai.tools.google_calendar import CalendarTool
from app.services.ai.tools.google_drive import DriveTool
from app.services.ai.tools.google_gmail import GmailTool
from app.services.ai.tools.google_tasks import GoogleTasksTool
from app.services.ai.tools.implementations.browser import BrowserAXTreeTool
from app.services.ai.tools.implementations.mcp_adapter import MCPAdapterTool
from app.services.ai.tools.memory_search import MemorySearchTool
from app.services.ai.tools.system_control import SystemControlTool
from app.services.ai.tools.app_launcher import AppLauncherTool
from app.services.ai.tools.browser import PlaywrightBrowserTool
from app.services.ai.tools.browser_automation import BrowserAutomationTool
from app.services.ai.tools.computer_control import ComputerControlTool
from app.services.ai.tools.notes_tool import NotesTool
from app.services.ai.tools.orchestrator import ToolOrchestrator

# Tools
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.reminders_tool import RemindersTool
from app.services.ai.tools.tasks_tool import TasksTool
from app.services.ai.tools.web_search import WebSearchTool

# Services
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.documents.chunking.text_chunker import (
    TextChunker,
)
from app.services.documents.extractors.registry import (
    ExtractorRegistry,
)

# Documents
from app.services.documents.processor import DocumentProcessor

#  Indexing
from app.services.indexing import IndexingService
from app.services.message_service import MessageService
from app.services.notes.note_service import NoteService
from app.services.reminders.reminder_service import ReminderService
from app.services.retrieval.fusion import ResultFusion
from app.services.retrieval.reranking import CrossEncoderReranker, Reranker
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.storage_service import StorageService
from app.services.tasks.task_service import TaskService

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


def get_note_repository(db: AsyncSession = Depends(get_db)) -> NoteRepository:
    return NoteRepository(db)

def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)

def get_reminder_repository(db: AsyncSession = Depends(get_db)) -> ReminderRepository:
    return ReminderRepository(db)


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
        from app.services.ai.providers.openai_provider import OpenAICompatibleProvider
        _router_instance = ProviderRouter()
        
        # 1. Google Gemini Native Providers (only real, available models)
        _router_instance.register_provider(GeminiProvider(model_name="gemini-3.5-flash", provider_name="gemini-3.5-flash"))
        _router_instance.register_provider(GeminiProvider(model_name="gemini-3.1-flash-lite", provider_name="gemini-3.1-flash-lite"))
        _router_instance.register_provider(GeminiProvider(model_name="gemini-2.5-flash", provider_name="gemini-2.5-flash"))
        _router_instance.register_provider(GeminiProvider(model_name="gemini-2.5-flash-lite", provider_name="gemini-2.5-flash-lite"))
        # gemini-flash is the canonical alias used by intent routing strategies
        _router_instance.register_provider(GeminiProvider(model_name="gemini-3.5-flash", provider_name="gemini-flash"))
        
        # 2. Local Ollama Native Providers — DISABLED (laptop resource constraints)
        # Uncomment to re-enable when running on a capable machine
        # _router_instance.register_provider(OllamaProvider(model_name="qwen2.5-coder:14b", provider_name="ollama-coder"))
        # _router_instance.register_provider(OllamaProvider(model_name="deepseek-r1", provider_name="ollama-reasoning"))
        # _router_instance.register_provider(OllamaProvider(model_name="qwen3:8b", provider_name="ollama-default"))
        
        # 3. Groq Fast OpenAI-Compatible Pipeline
        if settings.GROQ_API_KEY:
            groq_models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama-guard-3-8b",
                "qwen-2.5-32b",
                "qwen-2.5-coder-32b",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]
            for mdl in groq_models:
                p_name = mdl.split("/")[-1] if "/" in mdl else mdl
                _router_instance.register_provider(OpenAICompatibleProvider(
                    api_key=settings.GROQ_API_KEY, 
                    base_url="https://api.groq.com/openai/v1", 
                    model_name=mdl,
                    provider_name=f"groq-{p_name}"
                ))
            
        # 4. OpenRouter Scalable OpenAI-Compatible Pipeline
        if settings.OPENROUTER_API_KEY:
            openrouter_models = [
                "meta-llama/llama-3.3-70b-instruct",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "openai/gpt-oss-safeguard-20b",
                "canopylabs/orpheus-vl-english"
            ]
            for mdl in openrouter_models:
                p_name = mdl.split("/")[-1] if "/" in mdl else mdl
                _router_instance.register_provider(OpenAICompatibleProvider(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model_name=mdl, 
                    provider_name=f"openrouter-{p_name}"
                ))
            
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

def get_note_service(
    note_repository: NoteRepository = Depends(get_note_repository),
    document_repository: DocumentRepository = Depends(get_document_repository),
    document_processor: DocumentProcessor = Depends(get_document_processor),
) -> NoteService:
    return NoteService(note_repository, document_repository, document_processor)


def get_task_service(repo: TaskRepository = Depends(get_task_repository)) -> TaskService:
    return TaskService(repo)


def get_reminder_service(repo: ReminderRepository = Depends(get_reminder_repository)) -> ReminderService:
    return ReminderService(repo)

def get_google_tasks_service(db: AsyncSession = Depends(get_db)) -> GoogleTasksService:
    oauth_repo = OAuthRepository(db)
    auth_service = GoogleAuthService(oauth_repo)
    return GoogleTasksService(auth_service)


# ==========================================================
# Tool Orchestrator
# ==========================================================

def get_tool_orchestrator(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    memory_service: MemoryService = Depends(get_memory_service),
    note_service: NoteService = Depends(get_note_service),
    task_service: TaskService = Depends(get_task_service),
    reminder_service: ReminderService = Depends(get_reminder_service),
    db: AsyncSession = Depends(get_db),
) -> ToolOrchestrator:

    from app.services.ai.tools.weather import WeatherTool
    registry = ToolRegistry()
    registry.register(CurrentTimeTool())
    registry.register(WeatherTool())
    registry.register(CalculatorTool())
    registry.register(DocumentSearchTool(retrieval_service))
    registry.register(MemorySearchTool(memory_service))
    
    registry.register(NotesTool(note_service))
    registry.register(TasksTool(task_service))
    registry.register(RemindersTool(reminder_service))
    registry.register(MCPAdapterTool())
    registry.register(BrowserAXTreeTool())
    
    registry.register(SystemControlTool())
    registry.register(AppLauncherTool())
    registry.register(BrowserAutomationTool())
    registry.register(PlaywrightBrowserTool())
    registry.register(ComputerControlTool())
    
    if settings.GOOGLE_CLIENT_ID:
        oauth_repo = OAuthRepository(db)
        auth_service = GoogleAuthService(oauth_repo)
        registry.register(CalendarTool(GoogleCalendarService(auth_service)))
        registry.register(GmailTool(GoogleGmailService(auth_service)))
        registry.register(DriveTool(GoogleDriveService(auth_service)))
        registry.register(GoogleTasksTool(GoogleTasksService(auth_service)))
    
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

def get_ai_service_standalone(session) -> AIService:
    msg_repo = get_message_repository(session)
    conv_repo = get_conversation_repository(session)
    mem_repo = get_memory_repository(session)
    doc_repo = get_document_repository(session)
    chunk_repo = get_document_chunk_repository(session)
    note_repo = get_note_repository(session)
    task_repo = get_task_repository(session)
    remind_repo = get_reminder_repository(session)
    
    msg_svc = get_message_service(msg_repo, conv_repo)
    conv_svc = get_conversation_service(conv_repo)
    mem_svc = get_memory_service(mem_repo)
    
    embed_provider = get_embedding_provider()
    embed_svc = get_embedding_service(embed_provider)
    fusion = get_result_fusion()
    reranker = get_reranker()
    retrieval_svc = get_retrieval_service(chunk_repo, embed_svc, fusion, reranker)
    context_builder = get_context_builder(msg_svc, mem_svc, retrieval_svc)
    
    extractor_reg = get_extractor_registry()
    chunker = get_text_chunker()
    idx_svc = get_indexing_service(chunk_repo, doc_repo, embed_svc)
    doc_proc = get_document_processor(doc_repo, chunk_repo, extractor_reg, chunker, idx_svc)
    
    note_svc = get_note_service(note_repo, doc_repo, doc_proc)
    task_svc = get_task_service(task_repo)
    remind_svc = get_reminder_service(remind_repo)
    
    tool_orch = get_tool_orchestrator(retrieval_svc, mem_svc, note_svc, task_svc, remind_svc, session)
    
    provider = get_provider_router()
    return AIService(
        provider=provider,
        message_service=msg_svc,
        conversation_service=conv_svc,
        context_builder=context_builder,
        memory_service=mem_svc,
        tool_orchestrator=tool_orch
    )



# ==========================================================
# Authentication
# ==========================================================

async def get_current_user(
    request: Request,
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
        
    lat = request.headers.get('X-User-Lat')
    lon = request.headers.get('X-User-Lon')
    
    if lat and lon:
        try:
            f_lat = float(lat)
            f_lon = float(lon)
            if user.last_known_lat != f_lat or user.last_known_lon != f_lon:
                user.last_known_lat = f_lat
                user.last_known_lon = f_lon
                # The user object is attached to the session via the repository,
                # but to be completely safe, we should commit the change if we modified it.
                # However, since `get_current_user` is a dependency, committing here could 
                # interfere with the route's transaction. We will just set it and let the
                # route's transaction handle the commit if applicable, or do a safe targeted commit.
                repository.db.add(user)
                await repository.db.commit()
        except ValueError:
            pass

    return user

def boot_scheduler():
    from app.db.session import AsyncSessionLocal
    from app.services.notifications.notification_service import NotificationService
    from app.services.notifications.providers.database_provider import (
        DatabaseNotificationProvider,
    )
    from app.services.notifications.providers.push_provider import (
        PushNotificationProvider,
    )
    from app.services.scheduler.dispatcher import AgentDispatcher
    from app.services.scheduler.scheduler import BackgroundScheduler
    from app.services.scheduler.worker import SchedulerWorker

    async def worker_factory(session=None):
        db = session or AsyncSessionLocal()
        notification_service = NotificationService([
            DatabaseNotificationProvider(db),
            PushNotificationProvider(db)
        ])
        dispatcher = AgentDispatcher(
            planner=None, 
            executor=None, 
            notification_service=notification_service, 
            db=db
        )
        return SchedulerWorker(db, dispatcher)

    scheduler = BackgroundScheduler(worker_factory)
    scheduler.start()
    return scheduler