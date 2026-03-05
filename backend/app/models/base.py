import uuid

from sqlalchemy.orm import DeclarativeBase


def uuid7() -> uuid.UUID:
    """Generate a UUID v7 (time-sortable). Requires uuid6 package on Python < 3.13."""
    try:
        import uuid as _uuid

        return _uuid.uuid7()  # type: ignore[attr-defined]  # Python 3.13+
    except AttributeError:
        import uuid6  # type: ignore[import-untyped]

        return uuid6.uuid7()


class Base(DeclarativeBase):
    pass
