from app.core.config import settings
from app.services.email.base import EmailService
from app.services.email.resend_service import ResendEmailService


def get_email_service() -> EmailService:
    return ResendEmailService(
        api_key=settings.resend_api_key,
        from_email=settings.resend_from_email,
    )


__all__ = ["EmailService", "get_email_service"]
