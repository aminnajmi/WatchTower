"""Tidio unassigned live-chat monitoring and Telegram delivery."""

from __future__ import annotations

import html
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from .config import settings
from .integrations.tidio import get_unassigned_threads
from . import models
from .notifications.tidio_telegram import send as send_tidio_telegram

logger = logging.getLogger(__name__)


def _safe_text(value: object, fallback: str = "Unknown") -> str:
    text = str(value).strip() if value is not None else ""
    return html.escape(text[:500] or fallback)


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        return None


def format_alert(thread: dict, current_unassigned_count: int = 1) -> str:
    thread_id = _safe_text(thread.get("thread_id"))
    conversation_id = _safe_text(thread.get("conversation_id"))
    channel = _safe_text(thread.get("initial_message_channel"))
    intent = _safe_text(thread.get("thread_intent"), "Not detected")
    started = _safe_text(thread.get("thread_started_at"))
    return (
        "🚨 <b>WatchTower — New Tidio Unassigned Live Chat</b>\n\n"
        f"<b>Current unassigned live chats: {current_unassigned_count}</b>\n\n"
        f"Thread: <code>{thread_id}</code>\n"
        f"Conversation: <code>{conversation_id}</code>\n"
        f"Channel: {channel}\n"
        f"Intent: {intent}\n"
        f"Started: {started}\n\n"
        "⚠️ A new live chat is waiting in the Tidio unassigned queue."
    )


def _thread_id(thread: dict) -> str | None:
    value = thread.get("thread_id")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


async def check_unassigned_chats() -> dict:
    """Poll Tidio and notify only when a newly unassigned live chat appears.

    The current Tidio snapshot is treated as the source of truth for the
    unassigned queue. Existing unassigned chats remain active but do not cause
    another Telegram alert on every 10-second poll. When a chat disappears
    from the queue (for example, an agent takes it), it is marked inactive.
    If that same thread later becomes unassigned again, it is eligible for a
    new alert.
    """
    if not settings.tidio_enabled or not settings.tidio_telegram_enabled:
        return {
            "checked": 0,
            "current_unassigned": 0,
            "new_unassigned": 0,
            "notified": 0,
            "skipped": 0,
            "removed": 0,
            "errors": [],
        }

    threads = await get_unassigned_threads()
    current = {thread_id: thread for thread in threads if (thread_id := _thread_id(thread))}
    now = datetime.now(UTC).replace(tzinfo=None)

    db = models.SessionLocal()
    checked = notified = skipped = removed = 0
    errors: list[dict] = []
    try:
        existing_rows = {
            row.thread_id: row
            for row in db.scalars(select(models.TidioAlert)).all()
        }

        # Mark chats that disappeared from Tidio's current unassigned snapshot
        # as inactive. This is what allows a later reassignment to generate a
        # fresh alert for the same thread.
        for row in existing_rows.values():
            if row.is_active and row.thread_id not in current:
                row.is_active = False
                row.last_seen_at = now
                removed += 1

        db.commit()

        current_unassigned_count = len(current)
        new_thread_ids = {
            thread_id for thread_id in current
            if existing_rows.get(thread_id) is None or not existing_rows[thread_id].is_active
        }
        for thread_id, thread in current.items():
            checked += 1
            row = existing_rows.get(thread_id)
            is_new = row is None or not row.is_active

            if not is_new:
                row.last_seen_at = now
                skipped += 1
                continue

            # Do not mark a chat active until Telegram delivery succeeds. If
            # delivery fails, the next 10-second poll retries the alert.
            try:
                result = await send_tidio_telegram(
                    format_alert(thread, current_unassigned_count)
                )
                if not result.success:
                    errors.append({
                        "thread_id": thread_id,
                        "error": result.error or "Telegram delivery failed",
                    })
                    continue
                if not result.sent:
                    continue

                if row is None:
                    row = models.TidioAlert(thread_id=thread_id)
                    db.add(row)

                row.conversation_id = (
                    str(thread.get("conversation_id"))
                    if thread.get("conversation_id") is not None else None
                )
                row.visitor_id = (
                    str(thread.get("visitor_id"))
                    if thread.get("visitor_id") is not None else None
                )
                row.thread_started_at = _parse_datetime(thread.get("thread_started_at"))
                row.message_id = (
                    str(thread.get("thread_first_message_id"))
                    if thread.get("thread_first_message_id") is not None else None
                )
                row.intent = str(thread.get("thread_intent")) if thread.get("thread_intent") else None
                row.channel = str(thread.get("initial_message_channel")) if thread.get("initial_message_channel") else None
                row.notified_at = now
                row.is_active = True
                row.last_seen_at = now
                db.commit()
                notified += 1
                logger.info(
                    "Tidio new unassigned notification sent thread_id=%s current_unassigned=%s",
                    thread_id,
                    current_unassigned_count,
                )
            except Exception as exc:
                db.rollback()
                errors.append({"thread_id": thread_id, "error": type(exc).__name__})
                logger.warning(
                    "Tidio notification failed thread_id=%s error=%s",
                    thread_id,
                    type(exc).__name__,
                )

        return {
            "checked": checked,
            "current_unassigned": current_unassigned_count,
            "new_unassigned": len(new_thread_ids),
            "notified": notified,
            "skipped": skipped,
            "removed": removed,
            "errors": errors,
        }
    finally:
        db.close()
