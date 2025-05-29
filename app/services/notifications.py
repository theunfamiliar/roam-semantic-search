import smtplib
from email.mime.text import MIMEText
import logging
from app.config import EMAIL_FROM, EMAIL_TO, SMTP_USER, SMTP_PASS

logger = logging.getLogger(__name__)

def send_email(subject: str, body: str) -> None:
    """
    Send email notifications.
    
    Args:
        subject: Email subject
        body: Email body text
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            logger.info(f"✅ Email sent: {subject}")
    except Exception as e:
        logger.error(f"❌ Failed to send email: {str(e)}")
        # Don't re-raise - email failures shouldn't break the app 