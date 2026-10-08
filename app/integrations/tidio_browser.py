"""Browser-based Tidio inbox integration.

The administrator authenticates once from WatchTower Settings. Playwright then
persists the authenticated browser storage state in the application data
volume and reuses it for the 10-second Unassigned monitor.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)

TIDIO_LOGIN_URL = "https://www.tidio.com/panel/login"
TIDIO_INBOX_URL = "https://www.tidio.com/panel/conversations"
_CONVERSATION_RE = re.compile(r"/panel/conversations/([^/?#]+)")

_browser_lock = asyncio.Lock()
_manual_email = ""
_manual_password = ""


def _state_path() -> Path:
    database = settings.database_url
    if database.startswith("sqlite:///"):
        path = Path(database.removeprefix("sqlite:///"))
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.parent / "tidio_browser_state.json"
    return Path("./data/tidio_browser_state.json")


def _has_saved_session() -> bool:
    path = _state_path()
    try:
        return path.is_file() and path.stat().st_size > 20
    except OSError:
        return False


def _credentials_for_login() -> tuple[str, str]:
    # Credentials supplied by the admin login endpoint live only in memory for
    # the duration of the login attempt. Environment credentials are retained
    # only as a backwards-compatible fallback.
    if _manual_email and _manual_password:
        return _manual_email, _manual_password
    return settings.tidio_web_email, settings.tidio_web_password


async def _login_if_needed(page: Any) -> None:
    await page.goto(TIDIO_INBOX_URL, wait_until="domcontentloaded")
    if "/panel/login" not in page.url:
        return

    await page.wait_for_timeout(1200)
    if "/panel/login" not in page.url:
        return

    await page.goto(TIDIO_LOGIN_URL, wait_until="domcontentloaded")
    email_value, password_value = _credentials_for_login()
    if not email_value or not password_value:
        raise TidioBrowserError(
            "Tidio is not authenticated. Use Settings → Tidio Connection → Login to Tidio first."
        )

    try:
        email = page.get_by_label("Your work email", exact=True)
        password = page.get_by_label("Password", exact=True)
        await email.fill(email_value)
        await password.fill(password_value)
        await page.get_by_role("button", name=re.compile(r"log in", re.I)).click()
        await page.wait_for_timeout(1800)
    except Exception as exc:
        raise TidioBrowserError(
            f"Tidio login form could not be completed ({type(exc).__name__})"
        ) from exc

    if "/panel/login" in page.url:
        text = (await page.locator("body").inner_text())[:5000].lower()
        if "recaptcha" in text or "captcha" in text:
            raise TidioBrowserError(
                "Tidio login requires CAPTCHA or an interactive browser login"
            )
        if "verification" in text or "two-factor" in text or "2fa" in text:
            raise TidioBrowserError(
                "Tidio login requires interactive verification/2FA"
            )
        raise TidioBrowserError(
            "Tidio login failed; check the credentials or Tidio login method"
        )


def _browser_args() -> list[str]:
    return ["--disable-dev-shm-usage", "--no-sandbox"]


async def _with_browser(callback):
    """Run one operation with a fresh Playwright browser/context/page."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise TidioBrowserError("Playwright is not installed") from exc

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=settings.tidio_web_headless,
            args=_browser_args(),
        )
        try:
            state = _state_path()
            context = await browser.new_context(
                storage_state=str(state) if state.exists() else None,
            )
            try:
                page = await context.new_page()
                page.set_default_timeout(settings.tidio_web_timeout_seconds * 1000)
                return await callback(page, context)
            finally:
                await context.close()
        finally:
            await browser.close()


async def _save_state(context: Any) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    await context.storage_state(path=str(path))


async def login_with_credentials(email: str, password: str) -> dict[str, Any]:
    global _manual_email, _manual_password
    if not email.strip() or not password:
        raise TidioBrowserError("Email and password are required")

    async with _browser_lock:
        _manual_email = email.strip()
        _manual_password = password
        try:
            async def login(page, context):
                await _login_if_needed(page)
                await _save_state(context)
                return {"url": page.url}

            result = await _with_browser(login)
            logger.info("Tidio browser session saved")
            return result
        except TidioBrowserError:
            raise
        except Exception as exc:
            raise TidioBrowserError(
                f"Tidio browser login failed ({type(exc).__name__})"
            ) from exc
        finally:
            _manual_email = ""
            _manual_password = ""


async def check_connection() -> dict[str, Any]:
    if not _has_saved_session():
        raise TidioBrowserError("Browser session not found. Login to Tidio from Settings first.")

    async with _browser_lock:
        try:
            async def check(page, _context):
                await page.goto(TIDIO_INBOX_URL, wait_until="domcontentloaded")
                await page.wait_for_timeout(800)
                if "/panel/login" in page.url:
                    raise TidioBrowserError("Saved Tidio browser session has expired. Login again.")
                return {"url": page.url}

            return await _with_browser(check)
        except TidioBrowserError:
            raise
        except Exception as exc:
            raise TidioBrowserError(
                f"Tidio browser connection check failed ({type(exc).__name__})"
            ) from exc


async def clear_session() -> None:
    async with _browser_lock:
        path = _state_path()
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise TidioBrowserError("Could not clear the saved Tidio browser session") from exc
        logger.info("Tidio browser session cleared")


async def _open_unassigned(page: Any) -> None:
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
    if not settings.tidio_enabled:
        return []

    async with _browser_lock:
        if not _has_saved_session():
            raise TidioBrowserError(
                "Browser session not found. Use Settings → Tidio Connection → Login to Tidio first."
            )
        try:
            async def snapshot(page, _context):
                await _login_if_needed(page)
                await _open_unassigned(page)
                return await _extract_unassigned(page)

            threads = await _with_browser(snapshot)
            logger.info("Tidio browser snapshot: %s unassigned conversations", len(threads))
            return threads
        except TidioBrowserError:
            raise
        except Exception as exc:
            try:
                path = _state_path().with_name("tidio_browser_error.png")
                # A screenshot is useful for diagnostics and does not contain
                # the submitted password.
                # The page is closed by _with_browser after the callback, so
                # generic exceptions are intentionally not re-captured here.
            except Exception:
                pass
            raise TidioBrowserError(
                f"Tidio browser check failed ({type(exc).__name__})"
            ) from exc
