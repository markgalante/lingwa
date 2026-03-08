import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import CompleteRegistration, LoginRequest, MessageResponse, TokenResponse, UserRead, UserRegister
from app.services.email import get_email_service

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/google/callback")
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    async with AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token",
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    async with AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user info from Google",
        )

    userinfo = userinfo_response.json()
    google_id: str = userinfo["sub"]
    email: str = userinfo["email"]
    name: str | None = userinfo.get("name")
    avatar_url: str | None = userinfo.get("picture")

    user = await crud_user.get_by_google_id(db, google_id)

    if not user:
        user = await crud_user.get_by_email(db, email)
        if user:
            user = await crud_user.update_google_fields(
                db, user, google_id=google_id, name=name, avatar_url=avatar_url
            )
        else:
            user = await crud_user.create_google_user(
                db, email=email, google_id=google_id, name=name, avatar_url=avatar_url
            )

    jwt_token = create_access_token(str(user.id))
    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={jwt_token}"
    )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    existing = await crud_user.get_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(hours=24)

    user = await crud_user.create_email_user(
        db,
        email=body.email,
        verification_token=token,
        verification_token_expires=expires,
    )

    await get_email_service().send_verification_email(user.email, token)

    return MessageResponse(message="Check your email to verify your account")


@router.post("/complete-registration", response_model=TokenResponse)
async def complete_registration(
    body: CompleteRegistration, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user = await crud_user.get_by_verification_token(db, body.token)

    if not user or not user.verification_token_expires:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification link")

    if datetime.now(UTC) > user.verification_token_expires.replace(tzinfo=UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired")

    user = await crud_user.complete_registration(
        db, user, name=body.name, hashed_password=hash_password(body.password)
    )
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await crud_user.get_by_email(db, body.email)
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
