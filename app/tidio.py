from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import time
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from .config import settings
from .models import SessionLocal, TidioConnection

logger = logging.getLogger(__name__)

TIDIO_LOGIN_URL = "https://www.tidio.com/panel/login"
POLL_SECONDS = 3
RECONNECT_DELAYS = (5, 15, 30, 60, 300, 300)


@dataclass
class TidioSnapshot:
    connected: bool
    status: str
    unassigned_count: int = 0
    last_checked_at: datetime | None = None
    error: str | None = None


class TidioMonitor:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._snapshot = TidioSnapshot(False, "not_configured")
        self._last_unassigned_ids: set[str] = set()
        self._reconnect_attempts = 0
        self._retry_at = 0.0

    @property
    def snapshot(self) -> TidioSnapshot:
        return self._snapshot

    def _fernet(self) -> Fernet:
        if not settings.tidio_encryption_key:
            raise RuntimeError("TIDIO_ENCRYPTION_KEY is required to save Tidio credentials")
        try:
            return Fernet(settings.tidio_encryption_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise RuntimeError("TIDIO_ENCRYPTION_KEY must be a valid Fernet key") from exc

    def encrypt_password(self, password: str) -> str:
        return self._fernet().encrypt(password.encode("utf-8")).decode("ascii")

    def decrypt_password(self, encrypted: str) -> str:
        try:
            return self._fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError("Stored Tidio credentials cannot be decrypted") from exc

    async def connect(self, username: str, password: str) -> TidioSnapshot:
        username = username.strip()
        if not username or not password:
            raise ValueError("Tidio username and password are required")
        try:
            self.encrypt_password(password)
        except RuntimeError as exc:
            self._snapshot = TidioSnapshot(False, "credentials_unavailable", error=str(exc))
            return self._snapshot

        async with self._lock:
            await self._stop_monitor_task()
            await self._close_browser()
            self._stop_event = asyncio.Event()
            self._reconnect_attempts = 0
            self._retry_at = 0.0
            self._snapshot = TidioSnapshot(False, "connecting")
            await self._save_credentials(username, password, "connecting", None)
            await self._set_enabled(True)
            try:
                await self._ensure_browser()
                await self._login(username, password)
                await self._check_once()
                await self._save_credentials(username, password, "connected", None)
                self._start_monitor_task()
                return self._snapshot
            except Exception as exc:
                logger.warning("Tidio connection failed stage=connect error_type=%s", type(exc).__name__)
                status = self._failure_status(exc)
                public_error = self._public_error(exc)
                await self._save_credentials(username, password, status, public_error)
                if status == "authentication_failed" or status == "manual_verification_required":
                    await self._set_enabled(False)
                self._snapshot = TidioSnapshot(False, status, error=public_error)
                await self._close_browser()
                if status == "reconnecting":
                    self._start_monitor_task()
                return self._snapshot

    async def shutdown(self) -> None:
        self._stop_event.set()
        await self._stop_monitor_task()
        self._stop_event.set()
        async with self._lock:
            await self._close_browser()

    async def disconnect(self) -> None:
        async with self._lock:
            await self._stop_monitor_task()
            await self._close_browser()
            db = SessionLocal()
            try:
                row = db.get(TidioConnection, 1)
                if row:
                    row.username = ""
                    row.password_encrypted = ""
                    row.enabled = False
                    row.status = "disconnected"
                    row.last_error = None
                    row.last_checked_at = None
                    row.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            self._snapshot = TidioSnapshot(False, "disconnected")
            self._last_unassigned_ids.clear()
            self._reconnect_attempts = 0
            self._retry_at = 0.0

    async def restore(self) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if not row or not row.enabled or not row.username or not row.password_encrypted:
                return
            username = row.username
            password = self.decrypt_password(row.password_encrypted)
        except Exception as exc:
            logger.warning("Tidio credential restore failed (%s)", type(exc).__name__)
            self._snapshot = TidioSnapshot(False, "credentials_unavailable", error="Stored credentials are unavailable")
            return
        finally:
            db.close()

        await self.connect(username, password)

    async def _ensure_browser(self) -> None:
        if self._context and self._page and not self._page.is_closed():
            return
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._browser is None:
            launch_kwargs = {
                "headless": True,
            }
            try:
                self._browser = await self._playwright.chromium.launch(**launch_kwargs)
            except Exception:
                logger.exception("Tidio Chromium launch failed; Playwright startup diagnostics follow")
                await self._close_browser()
                raise
        self._context = await self._browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="en-US",
        )
        self._page = await self._context.new_page()

    async def _login(self, username: str, password: str) -> None:
        assert self._page is not None
        page = self._page
        await page.goto(TIDIO_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
        await page.locator('input[autocomplete="username"], input[type="email"], input[name="username"]').first.fill(username)
        await page.locator('input[type="password"]').first.fill(password)
        await page.get_by_role("button", name=re.compile(r"log in", re.I)).first.click()
        await page.wait_for_timeout(2_000)
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        if "/panel/login" in urlparse(page.url).path:
            body = (await page.locator("body").inner_text()).lower()
            if "recaptcha" in body or "two-factor" in body or "verification" in body:
                raise RuntimeError("Tidio requires additional browser verification")
            raise RuntimeError("Tidio rejected the supplied credentials")
        await self._open_inbox()

    async def _open_inbox(self) -> None:
        assert self._page is not None
        page = self._page
        try:
            inbox = page.get_by_text("Inbox", exact=True).first
            if await inbox.is_visible(timeout=2_000):
                await inbox.click()
                await page.wait_for_timeout(500)
        except Exception:
            # The login destination may already be the Inbox. Monitoring will
            # validate the presence of the Unassigned view on the next check.
            pass

    def _start_monitor_task(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._monitor_loop(), name="tidio-monitor")

    async def _stop_monitor_task(self) -> None:
        task, self._task = self._task, None
        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                async with self._lock:
                    await self._check_once()
                    self._reconnect_attempts = 0
                    self._retry_at = 0.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Tidio monitor check failed error_type=%s", type(exc).__name__)
                status = self._failure_status(exc)
                public_error = self._public_error(exc)
                if status == "manual_verification_required" or status == "authentication_failed":
                    self._snapshot = TidioSnapshot(False, status, error=public_error)
                    await self._set_status(status, public_error)
                    await self._stop_monitor_task()
                    return
                if self._reconnect_attempts >= len(RECONNECT_DELAYS):
                    self._snapshot = TidioSnapshot(False, "reconnect_paused", error="Automatic reconnect paused after repeated failures. Reconnect manually.")
                    await self._set_status("reconnect_paused", self._snapshot.error)
                    await self._stop_monitor_task()
                    return
                if time.monotonic() >= self._retry_at:
                    async with self._lock:
                        await self._reconnect(public_error)
            try:
                delay = max(0.0, self._retry_at - time.monotonic())
                await asyncio.wait_for(self._stop_event.wait(), timeout=max(POLL_SECONDS, min(delay, POLL_SECONDS)))
            except asyncio.TimeoutError:
                pass

    async def _reconnect(self, previous_error: str) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if not row or not row.password_encrypted:
                return
            username = row.username
            password = self.decrypt_password(row.password_encrypted)
        except Exception:
            return
        finally:
            db.close()

        self._snapshot = TidioSnapshot(False, "reconnecting", error=previous_error)
        try:
            await self._close_browser()
            await self._ensure_browser()
            await self._login(username, password)
            await self._check_once()
            await self._save_credentials(username, password, "connected", None)
            self._reconnect_attempts = 0
            self._retry_at = 0.0
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._reconnect_attempts += 1
            status = self._failure_status(exc)
            public_error = self._public_error(exc)
            if status == "reconnecting":
                delay = RECONNECT_DELAYS[min(self._reconnect_attempts - 1, len(RECONNECT_DELAYS) - 1)]
                self._retry_at = time.monotonic() + delay
                logger.warning("Tidio reconnect failed error_type=%s retry_in_seconds=%s", type(exc).__name__, delay)
            else:
                logger.warning("Tidio reconnect stopped status=%s error_type=%s", status, type(exc).__name__)
            self._snapshot = TidioSnapshot(False, status, error=public_error)
            await self._set_status(status, public_error)
            await self._close_browser()
            if status in {"authentication_failed", "manual_verification_required"}:
                await self._set_enabled(False)
                self._stop_event.set()

    async def _check_once(self) -> None:
        if not self._page or self._page.is_closed():
            raise RuntimeError("Tidio browser session is unavailable")
        if "/panel/login" in urlparse(self._page.url).path:
            raise RuntimeError("Tidio session expired")

        # Tidio's inbox UI is dynamic. We intentionally use visible text rather
        # than private/internal CSS class names so minor frontend changes are
        # less likely to break monitoring.
        body = await self._page.locator("body").inner_text(timeout=10_000)
        if "unassigned" not in body.lower():
            raise RuntimeError("Tidio inbox/unassigned view is unavailable")

        count = await self._read_unassigned_count()
        now = datetime.utcnow()
        self._snapshot = TidioSnapshot(True, "connected", count, now)
        await self._touch_status(now, None)

    async def _read_unassigned_count(self) -> int:
        assert self._page is not None
        page = self._page
        candidates = page.get_by_text(re.compile(r"^unassigned(?:\s+\d+)?$", re.I))
        count = await candidates.count()
        for index in range(count):
            text = (await candidates.nth(index).inner_text()).strip()
            match = re.search(r"\b(\d+)\b", text)
            if match:
                return int(match.group(1))

        # If the navigation label contains no count, inspect nearby buttons/links.
        for selector in ("button", "a"):
            nodes = page.locator(selector).filter(has_text=re.compile(r"unassigned", re.I))
            node_count = await nodes.count()
            for index in range(node_count):
                text = (await nodes.nth(index).inner_text()).strip()
                match = re.search(r"\b(\d+)\b", text)
                if match:
                    return int(match.group(1))
        return 0

    async def _save_credentials(self, username: str, password: str, status: str, error: str | None) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            encrypted = self.encrypt_password(password)
            now = datetime.utcnow()
            if row is None:
                row = TidioConnection(
                    id=1,
                    username=username,
                    password_encrypted=encrypted,
                    status=status,
                    last_error=error,
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
            else:
                row.username = username
                row.password_encrypted = encrypted
                row.status = status
                row.last_error = error
                row.updated_at = now
            db.commit()
        finally:
            db.close()

    async def _set_enabled(self, enabled: bool) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if row:
                row.enabled = enabled
                row.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    async def _touch_status(self, checked_at: datetime, error: str | None) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if row:
                row.status = "connected"
                row.last_checked_at = checked_at
                row.last_error = error
                row.updated_at = checked_at
                db.commit()
        finally:
            db.close()

    async def _set_status(self, status: str, error: str | None) -> None:
        db = SessionLocal()
        try:
            row = db.get(TidioConnection, 1)
            if row:
                row.status = status
                row.last_error = error
                row.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    async def _close_browser(self) -> None:
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        self._context = None
        self._page = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._playwright = None

    @staticmethod
    def _failure_status(exc: Exception) -> str:
        message = str(exc).lower()
        if any(marker in message for marker in ("verification", "recaptcha", "captcha", "two-factor", "two factor", "mfa")):
            return "manual_verification_required"
        if "rejected the supplied credentials" in message:
            return "authentication_failed"
        return "reconnecting"

    @staticmethod
    def _public_error(exc: Exception) -> str:
        message = str(exc).lower()
        if any(marker in message for marker in ("verification", "recaptcha", "captcha", "two-factor", "two factor", "mfa")):
            return "Tidio requires manual verification (MFA/CAPTCHA)."
        if "rejected the supplied credentials" in message:
            return "Tidio rejected the supplied credentials."
        if "browser" in message or "target page" in message:
            return "Tidio browser automation failed. Check server logs for Chromium startup details."
        return "Tidio check failed. Check server logs for details."


monitor = TidioMonitor()
