import asyncio
from functools import partial

import resend

from app.services.email import templates
from app.services.email.base import EmailService


class ResendEmailService(EmailService):
    def __init__(self, api_key: str, from_email: str) -> None:
        resend.api_key = api_key
        self._from = from_email

    async def send_verification_email(self, to: str, token: str) -> None:
        await self._send(
            to=to,
            subject="Verify your email address at Lingwa",
            html=templates.verification_email(token),
        )

    async def send_password_reset_email(self, to: str, token: str) -> None:
        await self._send(
            to=to,
            subject="Reset your Lingwa password",
            html=templates.password_reset_email(token),
        )

    async def _send(self, *, to: str, subject: str, html: str) -> None:
        """Wraps the synchronous Resend SDK call in a thread so it doesn't block the event loop."""
        send = partial(
            resend.Emails.send,
            {"from": self._from, "to": to, "subject": subject, "html": html},
        )
        await asyncio.to_thread(send)
