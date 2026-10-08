"""Tidio Analytics integration for detecting unanswered human-agent threads."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from ..config import settings
from .tidio_browser import get_unassigned_threads as get_browser_unassigned_threads

logger = logging.getLogger(__name__)

TIDIO_ANALYTICS_URL = "https://taa.data.tidio.com/agent_thread_details"


class TidioConfigurationError(RuntimeError):
    pass


async def get_unassigned_threads() -> list[dict]:
    """Return recent human-agent threads that Tidio marks as missed/unanswered.

    Tidio's public Analytics API does not expose the live Unassigned inbox as a
    direct OpenAPI resource. It does expose `ind_missed_thread`, which indicates
    a human-agent thread that was not replied to. We use that supported signal
    together with an open-thread check as the notification trigger.
    """
    if not settings.tidio_enabled:
        return []
    # Browser mode is used when Developer/OpenAPI credentials are not configured.
    # Authentication is established from the admin Settings page and persisted
    # in the application data volume.
    if not (settings.tidio_client_id and settings.tidio_client_secret):
        return await get_browser_unassigned_threads()

    lookback = max(1, settings.tidio_lookback_minutes)
    since = (datetime.now(timezone.utc) - timedelta(minutes=lookback)).isoformat().replace("+00:00", "Z")
    params = {
        "select": "_unique_id,thread_id,thread_started_at,thread_ended_at,conversation_id,visitor_id,thread_first_message_id,thread_last_message_id,ind_missed_thread,thread_intent,initial_message_channel",
        "thread_started_at": f"gte.{since}",
        "ind_missed_thread": "eq.1",
        "thread_ended_at": "is.null",
        "order": "thread_started_at.asc",
        "limit": "100",
    }
    headers = {
        "X-Tidio-Openapi-Client-Id": settings.tidio_client_id,
        "X-Tidio-Openapi-Client-Secret": settings.tidio_client_secret,
        "Accept": "application/json",
        "Prefer": "count=none",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.get(TIDIO_ANALYTICS_URL, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Tidio Analytics API returned HTTP {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Tidio Analytics request failed ({type(exc).__name__})") from exc
    except ValueError as exc:
        raise RuntimeError("Tidio Analytics API returned invalid JSON") from exc

    if not isinstance(payload, list):
        raise RuntimeError("Tidio Analytics API returned an unexpected response")
    return [item for item in payload if isinstance(item, dict) and item.get("thread_id") is not None]
