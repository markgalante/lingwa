import uuid

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


async def create_email_user(
    db: AsyncSession,
    *,
    email: str,
    hashed_password: str,
    name: str | None,
) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
        name=name,
        is_verified=False,
    )
    db.add(user)
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
