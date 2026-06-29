from app.core.exceptions import UserAlreadyExistsException
from app.core.exceptions import InvalidCredentialsException
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.utils.jwt import create_access_token
from app.utils.security import verify_password
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
    
    async def login(self, email: str, password: str) -> str:
        user = await self.repository.get_by_email(email)

        if not user:
            raise InvalidCredentialsException(
                "Invalid email or password"
            )

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise InvalidCredentialsException(
                "Invalid email or password"
            )

        return create_access_token(user.id)