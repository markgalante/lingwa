"""
Quick smoke-test for the email service. Run from the backend/ directory:

    python test_email.py your@email.com
"""

import asyncio
import sys


async def main(to: str) -> None:
    from app.services.email import get_email_service

    svc = get_email_service()
    print(f"Sending verification email to {to} ...")
    await svc.send_verification_email(to=to, token="test-token-abc123")
    print("Done. Check your inbox.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_email.py your@email.com")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
