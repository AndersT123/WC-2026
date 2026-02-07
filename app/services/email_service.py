from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def create_magic_link_email_html(username: str, magic_link: str, action: str = "login") -> str:
    """
    Create HTML content for magic link email.

    Args:
        username: User's username (or email for login)
        magic_link: Full magic link URL
        action: Action type - "login" or "logout"

    Returns:
        HTML email content
    """
    if action == "logout":
        button_text = "Confirm Logout"
        subject_text = "Confirm Logout"
        message_text = "Click the button below to confirm logout. This link will expire in 15 minutes."
    else:
        button_text = "Sign In"
        subject_text = "Your Magic Link"
        message_text = "Click the button below to sign in to your account. This link will expire in 15 minutes."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject_text}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
            <h1 style="color: #007bff; margin-top: 0;">World Cup Predictions</h1>
            <h2 style="color: #333; margin-bottom: 20px;">{subject_text}</h2>

            <p>Hi {username},</p>

            <p>{message_text}</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{magic_link}"
                   style="background-color: #007bff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">
                    {button_text}
                </a>
            </div>

            <p style="color: #666; font-size: 14px;">
                If the button doesn't work, copy and paste this link into your browser:
            </p>
            <p style="background-color: #fff; padding: 10px; border-radius: 4px; word-break: break-all; font-size: 12px;">
                {magic_link}
            </p>

            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

            <p style="color: #666; font-size: 12px; margin-bottom: 0;">
                If you didn't request this email, you can safely ignore it.
            </p>
        </div>

        <p style="color: #999; font-size: 12px; text-align: center;">
            &copy; 2026 World Cup Predictions. All rights reserved.
        </p>
    </body>
    </html>
    """


async def send_magic_link_email(
    email: str,
    token: str,
    username: Optional[str] = None,
    action: str = "login"
) -> bool:
    """
    Send magic link email via SMTP (Brevo).

    Args:
        email: Recipient email address
        token: Magic link token
        username: Username (for personalization)
        action: Action type - "login" or "logout"

    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.smtp_user or not settings.smtp_password:
        # For development/testing without email service configured
        print(f"\n{'='*60}")
        print(f"MAGIC LINK EMAIL (Email service not configured)")
        print(f"{'='*60}")
        print(f"To: {email}")
        print(f"Username: {username or email}")
        print(f"Action: {action}")
        link_suffix = f"&action={action}" if action != "login" else ""
        print(f"Magic Link: {settings.frontend_url}/auth/verify?token={token}{link_suffix}")
        print(f"{'='*60}\n")
        return True

    try:
        # Construct magic link URL
        link_suffix = f"&action={action}" if action != "login" else ""
        magic_link = f"{settings.frontend_url}/auth/verify?token={token}{link_suffix}"

        # Create email content
        display_name = username or email.split("@")[0]
        html_content = create_magic_link_email_html(display_name, magic_link, action)

        # Create MIME message
        message = MIMEMultipart("alternative")
        if action == "logout":
            message["Subject"] = "Confirm Logout - World Cup Predictions"
        else:
            message["Subject"] = "Your Magic Link - World Cup Predictions"
        message["From"] = settings.from_email
        message["To"] = email

        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send via SMTP
        print(f"\n{'='*60}")
        print(f"SENDING EMAIL VIA BREVO SMTP")
        print(f"{'='*60}")
        print(f"From: {settings.from_email}")
        print(f"To: {email}")
        print(f"Action: {action}")
        print(f"Server: {settings.smtp_host}:{settings.smtp_port}")

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)

        print(f"✓ Email sent successfully!")
        print(f"{'='*60}\n")
        return True

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"Error sending email: {str(e)}")
        print(f"{'='*60}\n")
        return False
