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

def get_llm_provider():
    return GeminiProvider()


def get_ai_service(
    provider: GeminiProvider = Depends(
        get_llm_provider,
    ),
) -> AIService:
    return AIService(provider)