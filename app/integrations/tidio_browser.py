"""Browser-based Tidio inbox integration.

This is the fallback for Tidio accounts that cannot access Developer/OpenAPI.
It uses the same web interface a human operator uses, keeps a persistent
browser session in the WatchTower data volume, and reads the Unassigned queue.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..config import settings

logger = logging.getLogger(__name__)

TIDIO_LOGIN_URL = "https://www.tidio.com/panel/login"
TIDIO_INBOX_URL = "https://www.tidio.com/panel/conversations"
_CONVERSATION_RE = re.compile(r"/panel/conversations/([^/?#]+)")


class TidioBrowserError(RuntimeError):
    pass


_browser_lock = asyncio.Lock()
_playwright = None
_browser = None
_context = None
_page = None


def _state_path() -> Path:
    database = settings.database_url
    if database.startswith("sqlite:///"):
        path = Path(database.removeprefix("sqlite:///"))
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.parent / "tidio_browser_state.json"
    return Path("./data/tidio_browser_state.json")


def _credentials_ready() -> bool:
    return bool(settings.tidio_web_email and settings.tidio_web_password)


async def _close_browser() -> None:
    global _playwright, _browser, _context, _page
    try:
        if _context is not None:
            await _context.close()
    except Exception:
        pass
    try:
        if _browser is not None:
            await _browser.close()
    except Exception:
        pass
    try:
        if _playwright is not None:
            await _playwright.stop()
    except Exception:
        pass
    _playwright = _browser = _context = _page = None


async def _start_browser() -> Any:
    global _playwright, _browser, _context, _page
    if _page is not None and not _page.is_closed():
        return _page

    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise TidioBrowserError("Playwright is not installed") from exc

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=settings.tidio_web_headless,
        args=["--disable-dev-shm-usage", "--no-sandbox"],
    )

    state = _state_path()
    state_arg = str(state) if state.exists() else None
    _context = await _browser.new_context(storage_state=state_arg)
    _page = await _context.new_page()
    _page.set_default_timeout(settings.tidio_web_timeout_seconds * 1000)
    return _page


async def _save_state() -> None:
    if _context is None:
        return
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    await _context.storage_state(path=str(path))


def _looks_logged_out(url: str) -> bool:
    return "/panel/login" in url


async def _login_if_needed(page: Any) -> None:
    await page.goto(TIDIO_INBOX_URL, wait_until="domcontentloaded")
    if not _looks_logged_out(page.url):
        return

    # A persisted session may still be valid but Tidio can render the login
    # page briefly before restoring it. Give the app a short chance to settle.
    await page.wait_for_timeout(1200)
    if not _looks_logged_out(page.url):
        return

    await page.goto(TIDIO_LOGIN_URL, wait_until="domcontentloaded")

    if not _credentials_ready():
        raise TidioBrowserError("TIDIO_WEB_EMAIL and TIDIO_WEB_PASSWORD are required")

    try:
        email = page.get_by_label("Your work email", exact=True)
        password = page.get_by_label("Password", exact=True)
        await email.fill(settings.tidio_web_email)
        await password.fill(settings.tidio_web_password)
        await page.get_by_role("button", name=re.compile(r"log in", re.I)).click()
        await page.wait_for_timeout(1500)
    except Exception as exc:
        raise TidioBrowserError(f"Tidio login form could not be completed ({type(exc).__name__})") from exc

    if _looks_logged_out(page.url):
        text = (await page.locator("body").inner_text())[:4000].lower()
        if "recaptcha" in text or "captcha" in text:
            raise TidioBrowserError("Tidio login requires CAPTCHA or an interactive browser login")
        raise TidioBrowserError("Tidio login failed; check the web credentials or account login method")

    await _save_state()


async def _open_unassigned(page: Any) -> None:
    # Prefer the visible navigation item. This avoids hard-coding Tidio's
    # internal inbox route, which can change between panel versions.
    label = settings.tidio_web_unassigned_label
    candidates = page.get_by_text(label, exact=True)
    count = await candidates.count()
    for index in range(count):
        item = candidates.nth(index)
        try:
            if await item.is_visible():
                await item.click()
                await page.wait_for_timeout(500)
                return
        except Exception:
            continue

    # Fallback to the currently documented conversation route.
    await page.goto(TIDIO_INBOX_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(700)
    candidates = page.get_by_text(label, exact=True)
    count = await candidates.count()
    for index in range(count):
        item = candidates.nth(index)
        try:
            if await item.is_visible():
                await item.click()
                await page.wait_for_timeout(500)
                return
        except Exception:
            continue

    raise TidioBrowserError(f"Could not find Tidio '{label}' queue")


def _conversation_id_from_url(url: str) -> str | None:
    match = _CONVERSATION_RE.search(url)
    return match.group(1) if match else None


async def _extract_unassigned(page: Any) -> list[dict]:
    anchors = page.locator('a[href*="/panel/conversations/"]')
    count = await anchors.count()
    result: dict[str, dict] = {}
    for index in range(count):
        anchor = anchors.nth(index)
        try:
            href = await anchor.get_attribute("href")
            if not href:
                continue
            conversation_id = _conversation_id_from_url(href)
            if not conversation_id:
                continue
            text = (await anchor.inner_text()).strip()
            result.setdefault(
                conversation_id,
                {
                    "thread_id": conversation_id,
                    "conversation_id": conversation_id,
                    "conversation_url": href if href.startswith("http") else f"https://www.tidio.com{href}",
                    "summary": " ".join(text.split())[:500],
                    "source": "tidio_browser",
                },
            )
        except Exception:
            continue
    return list(result.values())


async def get_unassigned_threads() -> list[dict]:
    """Read the live Unassigned queue from the authenticated Tidio panel."""
    if not settings.tidio_enabled:
        return []
    if not _credentials_ready():
        raise TidioBrowserError("TIDIO_WEB_EMAIL and TIDIO_WEB_PASSWORD are required")

    async with _browser_lock:
        try:
            page = await _start_browser()
            await _login_if_needed(page)
            await _open_unassigned(page)
            threads = await _extract_unassigned(page)
            logger.info("Tidio browser snapshot: %s unassigned conversations", len(threads))
            return threads
        except TidioBrowserError:
            await _close_browser()
            raise
        except Exception as exc:
            # Capture a diagnostic without exposing credentials.
            try:
                if _page is not None:
                    await _page.screenshot(path=str(_state_path().with_name("tidio_browser_error.png")))
            except Exception:
                pass
            await _close_browser()
            raise TidioBrowserError(f"Tidio browser check failed ({type(exc).__name__})") from exc
