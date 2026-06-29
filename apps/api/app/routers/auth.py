from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from app.dependencies import get_auth_service
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserResponse,
)
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

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    try:
        token = await service.login(
            email=form_data.username,
            password=form_data.password,
        )

        return TokenResponse(
            access_token=token,
        )

    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )