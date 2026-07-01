from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.utils.jwt import create_access_token, decode_access_token

from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService

from app.repositories.message_repository import MessageRepository
from app.services.message_service import MessageService

from app.services.ai import AIService
from app.services.ai.providers import GeminiProvider
from app.services.ai.context import ContextBuilder
from app.services.ai.context.context_builder import ContextBuilder

from app.repositories.memory_repository import MemoryRepository
from app.services.ai.memory import (
    MemoryExtractor,
    MemoryService,
)

from app.repositories.document_repository import DocumentRepository
from app.services.documents.processor import DocumentProcessor

from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from apps.api.app.repositories.document_chunk_repository import DocumentChunkRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repository: UserRepository = Depends(get_user_repository),
):
    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await repository.get_by_id(int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

def get_llm_provider():
    return GeminiProvider()

def get_conversation_repository(
    db: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(db)


def get_conversation_service(
    repository: ConversationRepository = Depends(
        get_conversation_repository,
    ),
) -> ConversationService:
    return ConversationService(repository)


def get_message_repository(
    db: AsyncSession = Depends(get_db),
) -> MessageRepository:
    return MessageRepository(db)

def get_document_repository(
    db=Depends(get_db),
) -> DocumentRepository:
    return DocumentRepository(db)


def get_storage_service() -> StorageService:
    return StorageService()


def get_document_service(
    repository: DocumentRepository = Depends(
        get_document_repository,
    ),
    storage_service: StorageService = Depends(
        get_storage_service,
    ),
) -> DocumentService:

    return DocumentService(
        repository=repository,
        storage_service=storage_service,
    )


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


def get_memory_repository(
    db: AsyncSession = Depends(
        get_db,
    ),
) -> MemoryRepository:
    return MemoryRepository(db)

def get_memory_extractor(
    provider: GeminiProvider = Depends(
        get_llm_provider,
    ),
) -> MemoryExtractor:

    return MemoryExtractor(
        provider,
    )


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


def get_context_builder(
    message_service: MessageService = Depends(
        get_message_service,
    ),
    memory_service: MemoryService = Depends(
        get_memory_service,
    ),
) -> ContextBuilder:

    return ContextBuilder(
        message_service=message_service,
        memory_service=memory_service,
    )

def get_document_chunk_repository(
    db=Depends(get_db),
):
    return DocumentChunkRepository(db)

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

):

    return DocumentProcessor(

        document_repository,

        chunk_repository,

        extractor_registry,

        chunker,

    )

def get_ai_service(
    provider: GeminiProvider = Depends(
        get_llm_provider,
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
) -> AIService:

    return AIService(
        provider=provider,
        message_service=message_service,
        conversation_service=conversation_service,
        context_builder=context_builder,
        memory_service=memory_service,
    )



