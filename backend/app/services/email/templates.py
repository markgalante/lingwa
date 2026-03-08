"""
HTML email templates.

These are provider-agnostic — any EmailService implementation can use them.
"""

from app.core.config import settings


def verification_email(token: str) -> str:
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Verify your email</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;padding:40px;border:1px solid #e5e7eb;">
          <tr>
            <td>
              <h1 style="margin:0 0 8px;font-size:24px;color:#111827;">Verify your email</h1>
              <p style="margin:0 0 24px;font-size:15px;color:#6b7280;line-height:1.5;">
                Click the button below to verify your email address and activate your Lingwa account.
                This link expires in 24 hours.
              </p>
              <a href="{verify_url}"
                 style="display:inline-block;background:#4f46e5;color:#ffffff;text-decoration:none;
                        font-size:15px;font-weight:600;padding:12px 24px;border-radius:6px;">
                Verify email
              </a>
              <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;">
                If you didn't create a Lingwa account, you can safely ignore this email.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def password_reset_email(token: str) -> str:
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reset your password</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;padding:40px;border:1px solid #e5e7eb;">
          <tr>
            <td>
              <h1 style="margin:0 0 8px;font-size:24px;color:#111827;">Reset your password</h1>
              <p style="margin:0 0 24px;font-size:15px;color:#6b7280;line-height:1.5;">
                Click the button below to choose a new password for your Lingwa account.
                This link expires in 1 hour.
              </p>
              <a href="{reset_url}"
                 style="display:inline-block;background:#4f46e5;color:#ffffff;text-decoration:none;
                        font-size:15px;font-weight:600;padding:12px 24px;border-radius:6px;">
                Reset password
              </a>
              <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;">
                If you didn't request a password reset, you can safely ignore this email.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
