"""Poll Tidio's Analytics API and route new unassigned live chats to Sales."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from html import escape
import logging

import httpx
from sqlalchemy import select

from . import models
from .config import settings
from .notifications.tidio_telegram import TidioTelegramSendResult, send as send_tidio_telegram
from .models import TidioAlert

logger = logging.getLogger(__name__)

TIDIO_ANALYTICS_URL = "https://taa.data.tidio.com/agent_thread_details"


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


async def get_unassigned_threads() -> list[dict]:
    """Fetch recent active human live-chat threads using Tidio API credentials."""
    if not settings.tidio_client_id or not settings.tidio_client_secret:
        raise RuntimeError("TIDIO_CLIENT_ID and TIDIO_CLIENT_SECRET are required")
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.tidio_lookback_minutes)
    params = {
        "select": ",".join((
            "thread_id", "conversation_id", "visitor_id", "thread_started_at",
            "thread_ended_at", "thread_first_response_agent_id", "thread_intent",
            "initial_message_channel", "initial_message_actor",
        )),
        "thread_started_at": f"gte.{cutoff.isoformat()}",
        "order": "thread_started_at.desc",
        "limit": "1000",
    }
    headers = {
        "X-Tidio-Openapi-Client-Id": settings.tidio_client_id,
        "X-Tidio-Openapi-Client-Secret": settings.tidio_client_secret,
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(TIDIO_ANALYTICS_URL, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Tidio API returned HTTP {exc.response.status_code}") from None
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Tidio API request failed ({type(exc).__name__})") from None
    except (ValueError, TypeError) as exc:
        raise RuntimeError("Tidio API returned an invalid response") from None

    rows = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        raise RuntimeError("Tidio API returned an invalid response")
    return [row for row in rows if isinstance(row, dict) and _is_unassigned_live_chat(row)]


def _is_unassigned_live_chat(thread: dict) -> bool:
    if not thread.get("thread_id") or thread.get("thread_ended_at"):
        return False
    if thread.get("assigned_operator_id") or thread.get("assigned_department_id"):
        return False
    if thread.get("thread_first_response_agent_id"):
        return False
    channel = str(thread.get("initial_message_channel") or "").strip().lower().replace("_", "")
    return not channel or channel in {"livechat", "chat", "live"}


def format_alert(thread: dict) -> str:
    """Format an HTML-safe alert without including visitor message content."""
    thread_id = escape(str(thread.get("thread_id") or "unknown"))
    parts = [f"🟢 <b>New unassigned Tidio live chat</b>", f"Chat: <code>{thread_id}</code>"]
    intent = thread.get("thread_intent")
    if intent:
        parts.append(f"Intent: {escape(str(intent))}")
    conversation_id = thread.get("conversation_id")
    if conversation_id:
        safe_id = escape(str(conversation_id), quote=True)
        parts.append(f'<a href="https://www.tidio.com/panel/conversations/{safe_id}">Open conversation</a>')
    return "\n".join(parts)


async def check_unassigned_chats() -> dict:
    """Notify once on entry into Unassigned; assignment/re-entry is a new event."""
    result = {"unassigned": 0, "notified": 0, "skipped": 0, "errors": []}
    if not settings.tidio_enabled:
        return result
    try:
        threads = await get_unassigned_threads()
    except Exception as exc:
        safe_error = str(exc) if isinstance(exc, RuntimeError) else f"Tidio API request failed ({type(exc).__name__})"
        result["errors"].append(safe_error)
        logger.warning("Tidio chat poll failed error=%s", safe_error)
        return result

    unique_threads = {}
    for thread in threads:
        thread_id = str(thread.get("thread_id") or "").strip()
        if thread_id:
            unique_threads[thread_id] = thread
    result["unassigned"] = len(unique_threads)
    db = models.SessionLocal()
    try:
        rows = db.scalars(select(TidioAlert)).all()
        existing = {row.thread_id: row for row in rows}
        current_ids = set(unique_threads)
        now = datetime.utcnow()
        for thread_id, row in existing.items():
            if row.is_unassigned and thread_id not in current_ids:
                row.is_unassigned = False
                row.updated_at = now

        for thread_id, thread in unique_threads.items():
            row = existing.get(thread_id)
            if row and row.is_unassigned:
                result["skipped"] += 1
                continue
            if not settings.tidio_telegram_enabled:
                continue
            try:
                sent: TidioTelegramSendResult = await send_tidio_telegram(format_alert(thread))
            except Exception as exc:
                sent = TidioTelegramSendResult(False, False, f"Telegram delivery failed ({type(exc).__name__})")
            if not sent.success or not sent.sent:
                safe_error = sent.error or "Tidio Telegram delivery failed"
                result["errors"].append(safe_error)
                logger.warning("Tidio alert delivery failed error=%s", safe_error)
                continue
            if row is None:
                row = TidioAlert(thread_id=thread_id)
                db.add(row)
            row.conversation_id = str(thread.get("conversation_id")) if thread.get("conversation_id") is not None else None
            row.visitor_id = str(thread.get("visitor_id")) if thread.get("visitor_id") is not None else None
            row.thread_started_at = _parse_datetime(thread.get("thread_started_at"))
            row.is_unassigned = True
            row.notified_at = now
            row.updated_at = now
            result["notified"] += 1
        db.commit()
    except Exception as exc:
        db.rollback()
        result["errors"].append(f"Tidio alert state update failed ({type(exc).__name__})")
        logger.warning("Tidio alert state update failed error_type=%s", type(exc).__name__)
    finally:
        db.close()
    return result


class TidioService:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None
        self._check_lock = asyncio.Lock()
        self.last_checked_at: datetime | None = None
        self.last_error: str | None = None
        self.unassigned_count = 0

    @property
    def running(self) -> bool:
        return bool(self._task and not self._task.done())

    async def start(self) -> None:
        if not settings.tidio_enabled or self.running:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="tidio-support-sales-poller")

    async def shutdown(self) -> None:
        task, self._task = self._task, None
        if not task:
            return
        if self._stop_event:
            self._stop_event.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._stop_event = None

    async def check_once(self) -> dict:
        async with self._check_lock:
            result = await check_unassigned_chats()
            self.last_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.unassigned_count = result["unassigned"]
            self.last_error = "; ".join(result["errors"]) or None
            return result

    async def _run(self) -> None:
        while self._stop_event and not self._stop_event.is_set():
            try:
                await self.check_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.last_error = f"Tidio polling failed ({type(exc).__name__})"
                logger.warning("Tidio polling failed error_type=%s", type(exc).__name__)
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=max(1, settings.tidio_poll_interval_seconds)
                )
            except asyncio.TimeoutError:
                pass


tidio_service = TidioService()
