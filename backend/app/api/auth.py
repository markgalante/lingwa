from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import UserRead
from app.api.deps import get_current_user

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


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
