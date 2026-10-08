"""Dedicated Telegram delivery for Tidio alerts.

This deliberately uses a separate chat ID from the existing OS-release
notification path so Support Tech notifications remain unchanged.
"""

from dataclasses import dataclass
import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TidioTelegramSendResult:
    success: bool
    sent: bool
    error: str | None = None


def _failure(error: str) -> TidioTelegramSendResult:
    logger.warning("Tidio Telegram notification failed: %s", error)
    return TidioTelegramSendResult(False, False, error)


async def send(message: str) -> TidioTelegramSendResult:
    if not settings.tidio_telegram_enabled:
        return TidioTelegramSendResult(True, False)
    if not settings.telegram_bot_token:
        return _failure("TELEGRAM_BOT_TOKEN is required for Tidio Telegram notifications")
    if not settings.tidio_telegram_chat_id:
        return _failure("TIDIO_TELEGRAM_CHAT_ID is required for Tidio Telegram notifications")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                data={
                    "chat_id": settings.tidio_telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": "true",
                },
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
        return _failure(f"Telegram request failed ({type(exc).__name__})")

    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return _failure("Telegram API rejected the Tidio message")
    return TidioTelegramSendResult(True, True)


async def send_test() -> TidioTelegramSendResult:
    return await send("🧪 <b>WatchTower Tidio TEST</b>\n\nTidio Telegram notification test successful.")
