import logging

from .discord import send as send_discord
from .telegram import send as send_telegram, send_support_sales as send_support_sales_telegram

logger = logging.getLogger(__name__)


async def notify(message: str) -> tuple[bool, str | None]:
    """Deliver to configured channels independently; report aggregate success."""
    success = True
    errors = []

    try:
        await send_discord(message)
    except Exception as exc:
        success = False
        errors.append(f"Discord notification failed ({type(exc).__name__})")
        logger.warning("Discord notification failed: %s", type(exc).__name__)

    try:
        result = await send_telegram(message)
        if not result.success:
            success = False
            errors.append(result.error or "Telegram notification failed")
        elif result.sent:
            logger.info("Telegram notification sent")
    except Exception as exc:
        success = False
        errors.append(f"Telegram notification failed ({type(exc).__name__})")

    return success, "; ".join(errors) if errors else None

from .service import create_notification, metadata_for

__all__ = ["notify", "send_discord", "send_telegram", "send_support_sales_telegram", "create_notification", "metadata_for"]
