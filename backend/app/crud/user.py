import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.languages))
    )
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.languages))
    )
    return result.scalar_one_or_none()


async def get_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.google_id == google_id).options(selectinload(User.languages))
    )
    return result.scalar_one_or_none()


async def get_by_verification_token(db: AsyncSession, token: str) -> User | None:
    result = await db.execute(
        select(User).where(User.verification_token == token).options(selectinload(User.languages))
    )
    return result.scalar_one_or_none()


async def create_email_user(
    db: AsyncSession,
    *,
    email: str,
    verification_token: str,
    verification_token_expires: datetime,
) -> User:
    user = User(
        email=email,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_token_expires,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def set_verification_token(
    db: AsyncSession,
    user: User,
    *,
    token: str,
    expires: datetime,
) -> User:
    user.verification_token = token
    user.verification_token_expires = expires
    await db.commit()
    await db.refresh(user)
    return user


async def complete_registration(
    db: AsyncSession,
    user: User,
    *,
    name: str,
    hashed_password: str,
) -> User:
    user.name = name
    user.hashed_password = hashed_password
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await db.commit()
    await db.refresh(user)
    return user


async def create_google_user(
    db: AsyncSession,
    *,
    email: str,
    google_id: str,
    name: str | None,
    avatar_url: str | None,
) -> User:
    user = User(
        email=email,
        google_id=google_id,
        name=name,
        avatar_url=avatar_url,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_google_fields(
    db: AsyncSession,
    user: User,
    *,
    google_id: str,
    name: str | None,
    avatar_url: str | None,
) -> User:
    user.google_id = google_id
    if name:
        user.name = name
    if avatar_url:
        user.avatar_url = avatar_url
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user
