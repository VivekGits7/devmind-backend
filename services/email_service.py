import httpx

from config import settings
from logger import get_logger

logger = get_logger(__name__)


async def send_otp(email: str, otp: str) -> bool:
    """Send OTP to user's email via n8n webhook."""
    if not settings.EMAIL_N8N_WEBHOOK_URL:
        logger.warning(f"EMAIL_N8N_WEBHOOK_URL not configured. OTP for {email}: {otp}")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMAIL_N8N_WEBHOOK_URL,
                json={"email": email, "otp": otp},
            )
            response.raise_for_status()
            logger.info(f"OTP sent to {email}")
            return True
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}: {str(e)}")
        return False
