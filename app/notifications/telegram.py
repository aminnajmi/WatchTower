import logging
from dataclasses import dataclass

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramSendResult:
    success: bool
    sent: bool
    error: str | None = None


def _failure(error: str) -> TelegramSendResult:
    logger.warning("Telegram notification failed: %s", error)
    return TelegramSendResult(success=False, sent=False, error=error)


async def send(message: str) -> TelegramSendResult:
    """Send a Telegram message without exposing credentials in errors or logs."""
    if not settings.telegram_enabled:
        return TelegramSendResult(success=True, sent=False)

    if not settings.telegram_bot_token:
        return _failure("TELEGRAM_BOT_TOKEN is required when Telegram is enabled")
    if not settings.telegram_chat_id:
        return _failure("TELEGRAM_CHAT_ID is required when Telegram is enabled")

    # The token is part of Telegram's URL path. Never include the URL or raw
    # exception text in logs or returned errors.
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                data={"chat_id": settings.telegram_chat_id, "text": message},
            )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        return _failure(f"Telegram API returned HTTP {exc.response.status_code}")
    except httpx.HTTPError as exc:
        return _failure(f"Telegram network request failed ({type(exc).__name__})")
    except (ValueError, TypeError):
        return _failure("Telegram API returned an invalid response")
    except Exception as exc:
        # Avoid leaking exception text: HTTP client errors can contain the
        # request URL, which includes the bot token.
        return _failure(f"Telegram request failed ({type(exc).__name__})")

    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return _failure("Telegram API rejected the message")
    return TelegramSendResult(success=True, sent=True)


async def send_test() -> TelegramSendResult:
    return await send("🧪 WatchTower — TEST\n\nTelegram notification test successful.")
