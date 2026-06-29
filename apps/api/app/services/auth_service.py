from app.core.exceptions import UserAlreadyExistsException
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.utils.security import hash_password


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, user_data: UserCreate) -> User:
        existing_user = await self.repository.get_by_email(
            user_data.email
        )

        if existing_user:
            raise UserAlreadyExistsException(
                "Email already registered"
            )

        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
        )

        return await self.repository.create(user)