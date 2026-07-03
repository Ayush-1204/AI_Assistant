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
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.integrations.google.auth import GoogleAuthService
from app.repositories.oauth_repository import OAuthRepository


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

@router.get("/google/login")
async def google_login(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        repo = OAuthRepository(db)
        auth_svc = GoogleAuthService(repo)
        url = auth_svc.get_authorization_url()
        return {"authorization_url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@router.post("/google/callback")
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        repo = OAuthRepository(db)
        auth_svc = GoogleAuthService(repo)
        await auth_svc.exchange_code(code, user.id)
        return {"message": "Google account linked successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )