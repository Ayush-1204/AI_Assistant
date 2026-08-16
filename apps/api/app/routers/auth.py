import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from app.db.models.user import User
from app.dependencies import get_auth_service, get_current_user, get_db
from app.integrations.google.auth import GoogleAuthService
from app.repositories.oauth_repository import OAuthRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.utils.jwt import create_access_token
from app.utils.security import hash_password

# In-memory store for transferring volatile OAuth frontend ports across the redirect sequence
OAUTH_METADATA: dict[str, str] = {}


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
        from app.repositories.oauth_state_repository import OAuthStateRepository
        state_repo = OAuthStateRepository(db)
        state_token = await state_repo.create_state(user.id)
        
        repo = OAuthRepository(db)
        auth_svc = GoogleAuthService(repo)
        url = auth_svc.get_authorization_url(state=state_token)
        return {"authorization_url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Account linking callback — links Google to an existing logged-in user."""
    try:
        from app.repositories.oauth_state_repository import OAuthStateRepository
        state_repo = OAuthStateRepository(db)
        is_valid, user_id = await state_repo.consume_state(state)
        
        if not is_valid or not user_id:
            raise ValueError("Invalid or expired OAuth state token.")
            
        repo = OAuthRepository(db)
        auth_svc = GoogleAuthService(repo)
        await auth_svc.exchange_code(code, user_id)
        return {"message": "Google account linked successfully."}
    except ValueError as val_e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/google/init")
async def google_init(
    response: Response,
    frontend_url: str = "http://localhost:8080",
    db: AsyncSession = Depends(get_db),
):
    """
    PUBLIC endpoint — starts Google OAuth for sign-in/sign-up.
    No JWT required. Returns the Google authorization URL for the frontend
    to redirect the browser window to.
    """
    try:
        from app.repositories.oauth_state_repository import OAuthStateRepository
        state_repo = OAuthStateRepository(db)
        # Pass no user_id (None) — this is a public flow, user doesn't exist yet
        state_token = await state_repo.create_state()

        repo = OAuthRepository(db)
        auth_svc = GoogleAuthService(repo)
        url = auth_svc.get_authorization_url(state=state_token)
        
        # Save frontend redirect source in memory dictionary mapped to the state token
        # to guarantee safe traversal across the external redirect sequence
        OAUTH_METADATA[state_token] = frontend_url
        return {"authorization_url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/google/auth-callback")
async def google_auth_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """
    PUBLIC callback for sign-in/sign-up via Google.
    Fetches the Google user profile, finds or creates a local user, and
    returns a JWT — completing the Google login flow.
    """
    try:
        import httpx

        from app.repositories.oauth_state_repository import OAuthStateRepository

        state_repo = OAuthStateRepository(db)
        is_valid, marker_id = await state_repo.consume_state(state)
        if not is_valid:
            raise ValueError("Invalid or expired OAuth state token.")

        repo = OAuthRepository(db)
        auth_svc = GoogleAuthService(repo)

        # Exchange code for tokens without needing an existing user
        if not auth_svc.flow:
            raise ValueError("Google OAuth is not configured")
        auth_svc.flow.fetch_token(code=code)
        credentials = auth_svc.flow.credentials

        # Fetch Google profile info
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            profile = resp.json()

        google_email = profile.get("email")
        google_name = profile.get("name", google_email)

        if not google_email:
            raise ValueError("Could not retrieve email from Google profile")

        # Find or create user
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(google_email)
        if not user:
            user = User(
                email=google_email,
                full_name=google_name,
                # Random secure password — user will never need it
                hashed_password=hash_password(secrets.token_urlsafe(32)),
            )
            user = await user_repo.create(user)

        # Save/update OAuth tokens for this user
        await repo.save_or_update(
            user_id=user.id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            scopes=",".join(credentials.scopes) if credentials.scopes else None,
            expires_at=credentials.expiry,
            provider="google",
        )

        token = create_access_token(user.id, name=user.full_name)
        
        # Retrieve frontend origin from memory and clear it
        frontend_url = OAUTH_METADATA.pop(state, "http://localhost:8080")
        
        # Redirect back to Flutter Web with the JWT in the URL fragment
        redirect_uri = f"{frontend_url}/#/auth/callback?token={token}"
        
        return RedirectResponse(url=redirect_uri)

    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))