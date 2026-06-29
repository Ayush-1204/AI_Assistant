from fastapi import APIRouter, Depends, HTTPException, status
from app.core.exceptions import UserAlreadyExistsException
from app.dependencies import get_auth_service
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    try:
        created_user = await service.register(user)
        return created_user

    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )