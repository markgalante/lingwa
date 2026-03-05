import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Table, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid7

# Association table for the many-to-many User <-> Language relationship
UserLanguage = Table(
    "user_languages",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("language_id", ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    languages: Mapped[list["Language"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Language", secondary="user_languages", back_populates="users"
    )
