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
from app.schemas.user import (
    CompleteRegistration,
    LoginRequest,
    MessageResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
    UserRegister,
)
from app.services.email import get_email_service

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google/login", summary="Initiate Google OAuth", description="Redirects the browser to Google's consent screen.")
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


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    description="Exchanges the authorization code for tokens, upserts the user, and redirects to the frontend with a JWT.",
)
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


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start email registration",
    description="Creates an unverified account and sends a verification email. Step 1 of 3.",
)
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


@router.get(
    "/check-verification-token",
    response_model=MessageResponse,
    summary="Validate verification token",
    description="Checks that the email verification token exists and has not expired. Step 2 of 3.",
)
async def check_verification_token(token: str, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    user = await crud_user.get_by_verification_token(db, token)

    if not user or not user.verification_token_expires:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification link")

    if datetime.now(UTC) > user.verification_token_expires.replace(tzinfo=UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired")

    return MessageResponse(message="Token is valid")


@router.post(
    "/complete-registration",
    response_model=TokenResponse,
    summary="Complete email registration",
    description="Sets the user's name and password, marks the account verified, and returns a JWT. Step 3 of 3.",
)
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


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Issues a fresh token and resends the verification email. Use when the original link has expired.",
)
async def resend_verification(body: UserRegister, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    user = await crud_user.get_by_email(db, body.email)

    if not user or user.is_verified or user.google_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending account found for that email")

    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(hours=24)
    await crud_user.set_verification_token(db, user, token=token, expires=expires)
    await get_email_service().send_verification_email(user.email, token)

    return MessageResponse(message="Verification email sent")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Sends a password-reset email if the account exists and has a password set. Always returns 200 to prevent user enumeration.",
)
async def forgot_password(
    body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    user = await crud_user.get_by_email(db, body.email)
    if user and user.hashed_password:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(UTC) + timedelta(hours=1)
        await crud_user.set_reset_token(db, user, token=token, expires=expires)
        await get_email_service().send_password_reset_email(user.email, token)
    return MessageResponse(message="If that email has an account with a password, a reset link has been sent")


@router.get(
    "/check-reset-token",
    response_model=MessageResponse,
    summary="Validate password reset token",
    description="Checks that the password reset token exists and has not expired.",
)
async def check_reset_token(token: str, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    user = await crud_user.get_by_reset_token(db, token)

    if not user or not user.password_reset_token_expires:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset link")

    if datetime.now(UTC) > user.password_reset_token_expires.replace(tzinfo=UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link has expired")

    return MessageResponse(message="Token is valid")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Validates the reset token and sets a new password.",
)
async def reset_password(
    body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    user = await crud_user.get_by_reset_token(db, body.token)

    if not user or not user.password_reset_token_expires:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset link")

    if datetime.now(UTC) > user.password_reset_token_expires.replace(tzinfo=UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link has expired")

    await crud_user.reset_password(db, user, hashed_password=hash_password(body.password))
    return MessageResponse(message="Password reset successfully")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Email/password login",
    description="Validates credentials and returns a JWT access token.",
)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await crud_user.get_by_email(db, body.email)
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get(
    "/me",
    response_model=UserRead,
    summary="Current user",
    description="Returns the authenticated user's profile. Requires `Authorization: Bearer <token>`.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
